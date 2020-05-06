
import state, const, pygame, script, conf
from file import FileInterface

class LaytonMovieHandler(state.LaytonSubscreenWithFader):
    def __init__(self, indexMovie):
        state.LaytonSubscreenWithFader.__init__(self)
        self.screenBlockInput = True
        self.isScriptAwaitingExecution = True
        self.indexScriptCommand = 0
        self.scriptMovie = script.gdScript.fromData(FileInterface.getPackedData(FileInterface.PATH_ASSET_SCRIPT + "movie\\" + conf.LAYTON_ASSET_LANG + "\\movie.plz", "m" + str(indexMovie) + ".gds", version=1))
    
    def doOnUpdateCleared(self, gameClockDelta):
        super().doOnUpdateCleared(gameClockDelta)
        if self.indexScriptCommand < len(self.scriptMovie.commands):
            if self.isScriptAwaitingExecution:
                while not(self.isUpdateBlocked()) and self.indexScriptCommand < len(self.scriptMovie.commands):
                    self.isScriptAwaitingExecution = self.executeGdScriptCommand(self.scriptMovie.commands[self.indexScriptCommand])
                    self.indexScriptCommand += 1
                pygame.event.post(pygame.event.Event(const.ENGINE_SKIP_CLOCK, {const.PARAM:None}))
                    
        elif self.isScriptAwaitingExecution:    # Script ready to execute more code, so all tasks are finished and fading can happen
            pass

    def executeGdScriptCommand(self, command):
        print(command.opcode)
        print(command.operands)
        return True

if __name__ == "__main__":
    tempPlayerState = state.LaytonPlayerState()
    tempPlayerState.remainingHintCoins = 100
    state.play(LaytonMovieHandler(1), tempPlayerState)

