import pygame

class Match():

    MOVE_RADIUS = 5
    SHADOW_OFFSET = 2
    
    def __init__(self, surfaceMatch, surfaceShadow, posX, posY, rot):
        self.surfaceMatch = surfaceMatch
        self.surfaceShadow = surfaceShadow
        self.pos = (posX, posY)
        self.rot = -rot
        self.region = 32
        self.drawShadow = True

    def getRot(self):
        return -self.rot

    def draw(self, gameDisplay):
        if self.drawShadow:
            appliedSurface = pygame.transform.rotate(self.surfaceShadow, self.rot)
            x,y = self.pos
            x += Match.SHADOW_OFFSET; y += Match.SHADOW_OFFSET 
            appliedSurfaceRect = appliedSurface.get_rect(center=(x,y))
            gameDisplay.blit(appliedSurface, (appliedSurfaceRect.x, appliedSurfaceRect.y))
        appliedSurface = pygame.transform.rotate(self.surfaceMatch, self.rot)
        appliedSurfaceRect = appliedSurface.get_rect(center=self.pos)
        gameDisplay.blit(appliedSurface, (appliedSurfaceRect.x, appliedSurfaceRect.y))
    
    def wasClicked(self, mousePos):
        if self.pos[0] + self.tileFrame.get_width() >= mousePos[0] and mousePos[0] >= self.pos[0]:
            if self.pos[1] + self.tileFrame.get_height() >= mousePos[1] and mousePos[1] >= self.pos[1]:
                return True
        return False

class Tile():
    def __init__(self, sourceAnim, sourceAnimName):
        # Tiles are loaded from an animation so this can be shared
        if sourceAnim.setAnimationFromName(sourceAnimName):
            self.tileFrame = sourceAnim.frames[sourceAnim.animMap[sourceAnim.animActive].indices[0]]
        else:
            if len(sourceAnim.frames) >= sourceAnimName:
                self.tileFrame = sourceAnim.frames[sourceAnimName - 1]
            else:
                self.tileFrame = pygame.Surface((24,24))

    def draw(self, gameDisplay, pos):
        gameDisplay.blit(self.tileFrame, pos)
    
    def get_width(self):
        return self.tileFrame.get_width()
    
    def get_height(self):
        return self.tileFrame.get_height()

    def wasClicked(self, mousePos, pos):
        if pos[0] + self.tileFrame.get_width() >= mousePos[0] and mousePos[0] >= pos[0]:
            if pos[1] + self.tileFrame.get_height() >= mousePos[1] and mousePos[1] >= pos[1]:
                return True
        return False

class IndependentTile(Tile):
    def __init__(self, sourceAnim, sourceAnimName, x=0, y=0):
        Tile.__init__(self, sourceAnim, sourceAnimName)
        self.sourcePos = (x,y)
        self.reset()
    
    def reset(self):
        self.pos = self.sourcePos

    def draw(self, gameDisplay):
        gameDisplay.blit(self.tileFrame, self.pos)
    
    def wasClicked(self, mousePos):
        if self.pos[0] + self.tileFrame.get_width() >= mousePos[0] and mousePos[0] >= self.pos[0]:
            if self.pos[1] + self.tileFrame.get_height() >= mousePos[1] and mousePos[1] >= self.pos[1]:
                return True
        return False