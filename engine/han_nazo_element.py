import pygame, anim
from math import sqrt

class TraceLocation():
    def __init__(self, x, y, diameter, isAnswer):
        self.pos = (x, y)
        self.radius = diameter // 2
        self.isAnswer = isAnswer
    
    def wasClicked(self, mousePos):
        if sqrt(((mousePos[0] - self.pos[0]) ** 2) + ((mousePos[1] - self.pos[1]) ** 2)) <= self.radius:
            return True
        return False

class IndependentTile(anim.StaticImage):
    def __init__(self, sourceAnim, sourceAnimName, x=0, y=0):
        if sourceAnim.setAnimationFromName(sourceAnimName):
            anim.StaticImage.__init__(self, sourceAnim.frames[sourceAnim.animMap[sourceAnim.animActive].indices[0]], x=x, y=y, imageIsSurface=True)
        else:
            if sourceAnimName.isdigit() and len(sourceAnim.frames) >= int(sourceAnimName):
                # TODO - Make more resilient here
                anim.StaticImage.__init__(self, sourceAnim.frames[sourceAnimName - 1], x=x, y=y, imageIsSurface=True)
            else:
                anim.StaticImage.__init__(self, pygame.Surface((24,24)), x=x, y=y, imageIsSurface=True)
        self.sourcePos = (x,y)
        
    def reset(self):
        self.pos = self.sourcePos

class IndependentIndexedTile(IndependentTile):
    def __init__(self, sourceAnim, sourceAnimName, index, x=0, y=0):
        IndependentTile.__init__(self, sourceAnim, sourceAnimName, x, y)
        self.index = index

class IndependentTileRotateable(IndependentTile):

    RADIUS_ROTATE = 20
    RADIUS_MOVE = 10

    def __init__(self, sourceAnim, sourceAnimName, rot, x=0, y=0):
        IndependentTile.__init__(self, sourceAnim, sourceAnimName, x, y)
        self.sourceImage = self.image
        self.sourceRot = -rot
        self.rotImage = 0
        self.rotPending = -rot
    
    def update(self, gameClockDelta):   # Rotate the image to make it correct
        if self.rotImage != self.rotPending:
            self.image = pygame.transform.rotate(self.sourceImage, self.rotPending)
            self.rotImage = self.rotPending

    def draw(self, gameDisplay):
        gameDisplay.blit(self.image, self.image.get_rect(center=self.pos))

    def getRot(self):
        return - self.rot
    
    def setRot(self, rot):
        self.rotPending = - rot

    def reset(self):
        super().reset()
        self.rot = self.sourceRot
        self.image = self.sourceImage
    
    def wasClicked(self, mousePos):
        # Rotate the mousePos to fit the shape
        return False

class SlidingShape():

    def __init__(self, cornerPos, isLocked):
        self.isLocked = isLocked
        self.isBound = False
        self.rects = []
        self.bound = pygame.Rect(0,0,0,0)
        self.initialPos = cornerPos
        self.cornerTilePos = cornerPos
        self.image = None
    
    def reset(self):
        self.cornerTilePos = self.initialPos

    def addCollisionRect(self, corner, length, tileSize):
        self.rects.append(pygame.Rect(corner[0] * tileSize[0], corner[1] * tileSize[1],
                                      length[0] * tileSize[0], length[1] * tileSize[1]))
        self.bound = self.bound.union(pygame.Rect(corner[0], corner[1],
                                                  length[0], length[1]))

    def resolveCollisionRects(self, tileSize):
        output = []
        for rect in self.rects:
            tempCornerPos = (self.cornerTilePos[0] * tileSize[0],
                            self.cornerTilePos[1] * tileSize[1])
            output.append(rect.move(tempCornerPos))
        return output

    def doesIntersect(self, additionalShape, tileSize):
        for rect in self.resolveCollisionRects(tileSize):
            for addRect in additionalShape.resolveCollisionRects(tileSize):
                if rect.colliderect(addRect):
                    return True
        return False
    
    def wasClicked(self, pos, posCorner, tileSize):
        for rect in self.resolveCollisionRects(tileSize):
            rect = rect.move(posCorner)
            if rect.collidepoint(pos):
                return True
        return False

class RoseWall():
    def __init__(self, start, end):
        # TODO - Rearrange points to make them move positively, the rose wall logic only checks under these cases
        # TODO - These are unsigned anyway, right?
        self.posCornerStart = start
        self.posCornerEnd = end
    
    def isOnWall(self, pos):
        
        def testInBounds(pos):
            minX = [self.posCornerStart[0], self.posCornerEnd[0]]
            minY = [self.posCornerEnd[1], self.posCornerStart[1]]
            minX.sort()
            minY.sort()
            if (pos[0] >= minX[0] and pos[0] <= minX[1] and
                pos[1] >= minY[0] and pos[1] <= minY[1]):
                return True
            return False

        if testInBounds(pos):
            if pos == self.posCornerStart or pos == self.posCornerEnd:
                return True
            elif self.posCornerStart[0] == self.posCornerEnd[0]:
                # Vertical line
                return pos[0] == self.posCornerStart[0]
            elif self.posCornerStart[1] == self.posCornerEnd[1]:
                # Horizontal line
                return pos[1] == self.posCornerStart[1]
            else:
                gradWall = (self.posCornerEnd[1] - self.posCornerStart[1]) / (self.posCornerEnd[0] - self.posCornerStart[0])
                if pos[0] - self.posCornerStart[0] > 0:
                    gradPoint = (pos[1] - self.posCornerStart[1]) / (pos[0] - self.posCornerStart[0])
                    return gradWall == gradPoint or gradWall == -gradPoint
        return False

class Pancake(anim.StaticImage):
    def __init__(self, imagePath, weight, x=0, y=0, imageIsSurface=False, imageIsNull=False, imageNullDimensions=None):
        anim.StaticImage.__init__(self, imagePath, x, y, imageIsSurface, imageIsNull, imageNullDimensions)
        self.weight = weight