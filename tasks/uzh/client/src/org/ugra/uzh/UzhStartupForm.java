/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package org.ugra.uzh;

import javax.microedition.lcdui.*;

/**
 *
 * @author Administrator
 */
public class UzhStartupForm extends Form implements CommandListener {
    private UzhMIDlet midlet;
    private Command startCommand;
    private TextField secretField;

    public UzhStartupForm(UzhMIDlet midlet) {
        super("Uzh");
        this.midlet = midlet;
        startCommand = new Command("Start", Command.OK, 1);
        addCommand(startCommand);
        secretField = new TextField("Secret code", "", 6, TextField.NUMERIC);
        append(secretField);
        setCommandListener(this);
    }

    public void commandAction(Command c, Displayable d) {
        if (c == startCommand) {
            String secret = secretField.getString();
            if (secret.length() != 6) {
                return;
            }
            midlet.startGame(Long.parseLong(secret));
        }
    }
}
