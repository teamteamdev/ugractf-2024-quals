package org.ugra.uzh;

import javax.microedition.midlet.MIDlet;
import javax.microedition.lcdui.Display;

public class UzhMIDlet extends MIDlet {

    private Display display;

    public void startApp() {
        display = Display.getDisplay(this);
        UzhStartupForm startupForm = new UzhStartupForm(this);
        display.setCurrent(startupForm);
    }

    public void pauseApp() {
    }

    public void destroyApp(boolean unconditional) {
    }

    public void startGame(long secretCode) {
        UzhCanvas canvas = new UzhCanvas(secretCode);
        display.setCurrent(canvas);
    }
}
