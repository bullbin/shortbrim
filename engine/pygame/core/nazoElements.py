import pygame

class Match():

    SHADOW_OFFSET = 2
    
    def __init__(self, surfaceMatch, surfaceShadow, posX, posY, rot):
        self.surfaceMatch = surfaceMatch
        self.surfaceShadow = surfaceShadow
        self.pos = (posX, posY)
        self.rot = rot
        self.region = 32
        self.drawShadow = True

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
