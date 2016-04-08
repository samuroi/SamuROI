class MaskCreator(object):
    """Manages the interactive creation of masks. I.e. event handling, connecting and disconnecting slots."""

    @property
    def enabled(self):
        return self.clickslot is not None

    @enabled.setter
    def enabled(self, e):
        """If disabled while creating a mask, mask gets discarded."""
        if not self.enabled and e:
            self.__connect()
        elif self.enabled and not e:
            self.__disconnect()

    def __init__(self, axes, canvas, update, notify, enabled=False):
        """
            Arguments:
                axes, the axes where the interactive creation takes place
                canvas, the figure canvas, required to connec to signals
                update, a callable which will be called after adding a corner to the currently created polygon
                notify, a callable that will get evoked with the outline of a finished polygon.
                enabled, should mask creation be enabled from the begininig (default False)
        """
        self.axes = axes
        self.canvas = canvas
        self.update = update
        self.notify = notify
        self.clickslot = None
        self.keyslot = None

        # connect slots via property setter
        self.enabled = enabled

    def __connect(self):
        self.clickslot = self.canvas.mpl_connect('button_press_event', self.__onclick)
        self.keyslot = self.canvas.mpl_connect('key_press_event', self.__onkey)

    def __disconnect(self):
        if self.keyslot is not None:
            self.canvas.mpl_disconnect(self.clickslot)
            self.canvas.mpl_disconnect(self.keyslot)
            self.keyslot = None
            self.clickslot = None

    def onkey(self, event):
        """The slot that will get called when a key is pressed."""
        raise Exception("This function needs to be implemented in a base class.")

    def onclick(self, event):
        """The slot that will get called when clicked into the axes."""
        raise Exception("This function needs to be implemented in a base class.")

    def __onclick(self, event):
        # filter out all events of other axes
        if self.axes is not event.inaxes:
            return
        # filter out events when zoom or pan is active
        # if self.canvas.manager.toolbar._active == 'PAN':
        #     return
        # if self.canvas.manager.toolbar._active == 'ZOOM':
        #     return

        # forward call to baseclass event handling
        self.onclick(event)

    def __onkey(self, event):
        # forward call to baseclass event handling
        self.onkey(event)
