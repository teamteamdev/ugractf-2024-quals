package org.ugra.uzh;

import java.io.*;
import javax.microedition.lcdui.*;
import javax.microedition.io.*;

public class UzhCanvas extends Canvas implements Runnable {
    private static final int BORDER_WIDTH = 1;
    private static final int NEEDED_FRUITS = 10;

    private long secretCode;
    private Thread gameLoop;

    // Game state.
    private UzhWorld world;
    private ByteArrayOutputStream movesStream;
    private byte lastDirection = Point.RIGHT;

    // Scores state.
    private int lastScore = -1;
    private int highScore = 0;
    private String extraScore = "";

    // Drawing.
    private Font font;
    private Image drawingBuffer;
    private Graphics bufferGraphics;
    private int cellSize;
    private int fieldStartX;
    private int fieldStartY;
    private int innerWidth;
    private int innerHeight;

    public UzhCanvas(long secretCode) {
        this.secretCode = secretCode;
        int width = getWidth();
        int height = getHeight();

        font = Font.getDefaultFont();

        if (!isDoubleBuffered()) {
            drawingBuffer = Image.createImage(width, height);
            bufferGraphics = drawingBuffer.getGraphics();
            bufferGraphics.setFont(font);
        }

        int scoreWidth = font.stringWidth("999");

        int cellWidth = (width - 2 * BORDER_WIDTH - 2 - scoreWidth) / UzhWorld.CELLS_X;
        int cellHeight = (height - 2 * BORDER_WIDTH) / UzhWorld.CELLS_Y;
        cellSize = Math.min(cellWidth, cellHeight);
        int fieldStartMiddleX = (width - cellSize * UzhWorld.CELLS_X - 2 * BORDER_WIDTH) / 2;
        int fieldStartScoreX = width - cellSize * UzhWorld.CELLS_X - 2 * BORDER_WIDTH - 2 - scoreWidth;
        fieldStartX = Math.min(fieldStartMiddleX, fieldStartScoreX);
        fieldStartY = (height - cellSize * UzhWorld.CELLS_Y - 2 * BORDER_WIDTH) / 2;
        innerWidth = UzhWorld.CELLS_X * cellSize;
        innerHeight = UzhWorld.CELLS_Y * cellSize;
    }

    public void paint(Graphics g) {
        if (drawingBuffer != null) {
            paintGame(bufferGraphics);
            g.drawImage(drawingBuffer, 0, 0, Graphics.TOP | Graphics.LEFT);
        } else {
            g.setFont(font);
            paintGame(g);
        }
    }

    private void paintGame(Graphics g) {
        // Fill the screen.
        g.setColor(255, 255, 255);
        g.fillRect(0, 0, getWidth(), getHeight());

        if (world != null) {
            // Playing.
            paintWorld(g);
        } else {
            // Show high score.
            paintHighScore(g);
        }
    }

    private void paintWorld(Graphics g) {
        int width = getWidth();

        // Draw the border.
        g.setColor(0, 0, 0);
        g.fillRect(
                fieldStartX,
                fieldStartY,
                2 * BORDER_WIDTH + innerWidth,
                BORDER_WIDTH);
        g.fillRect(
                fieldStartX,
                fieldStartY,
                BORDER_WIDTH,
                2 * BORDER_WIDTH + innerHeight);
        g.fillRect(
                fieldStartX + BORDER_WIDTH + innerWidth,
                fieldStartY,
                BORDER_WIDTH,
                2 * BORDER_WIDTH + innerHeight);
        g.fillRect(
                fieldStartX,
                fieldStartY + BORDER_WIDTH + innerHeight,
                2 * BORDER_WIDTH + innerWidth,
                BORDER_WIDTH);

        // Draw the uzh.
        g.setColor(0, 255, 0);
        UzhBody.Segment segment = world.getBody().getTailSegment();
        do {
            switch (segment.direction) {
                case Point.LEFT:
                    fillCells(g, segment.head.x, segment.head.y, segment.length, (byte) 1);
                    break;
                case Point.RIGHT:
                    fillCells(g, (byte) (segment.head.x - segment.length + 1), segment.head.y, segment.length, (byte) 1);
                    break;
                case Point.DOWN:
                    fillCells(g, segment.head.x, segment.head.y, (byte) 1, segment.length);
                    break;
                case Point.UP:
                    fillCells(g, segment.head.x, (byte) (segment.head.y - segment.length + 1), (byte) 1, segment.length);
                    break;
                default:
                    throw new RuntimeException("Invalid direction");
            }
            segment = segment.next;
        } while (segment != null);

        // Draw the fruit.
        g.setColor(244, 193, 0);
        Point fruit = world.getFruit();
        fillCells(g, fruit.x, fruit.y, (byte) 1, (byte) 1);

        // Draw the current score.
        g.setColor(0, 0, 0);
        g.drawString(String.valueOf(world.getEatenFruits()), width - 1, fieldStartY, Graphics.RIGHT | Graphics.TOP);
    }

    private void fillCells(Graphics g, byte x, byte y, byte width, byte height) {
        g.fillRect(
            fieldStartX + BORDER_WIDTH + x * cellSize,
            fieldStartY + BORDER_WIDTH + (UzhWorld.CELLS_Y - height - y) * cellSize,
            width * cellSize,
            height * cellSize
        );
    }

    private void paintHighScore(Graphics g) {
        int width = getWidth();
        int height = getHeight();
        int fontHeight = font.getHeight();

        g.setColor(0, 0, 0);

        int xPosition = width / 2;
        int yPosition = height / 3;
        {
            g.drawString("High score:", xPosition, yPosition, Graphics.HCENTER | Graphics.TOP);
            yPosition += fontHeight;
            g.drawString(String.valueOf(highScore), xPosition, yPosition, Graphics.HCENTER | Graphics.TOP);
        }

        yPosition += fontHeight + fontHeight / 2;
        if (lastScore >= 0) {
            g.drawString("Last score:", xPosition, yPosition, Graphics.HCENTER | Graphics.TOP);
            yPosition += fontHeight;
            g.drawString(String.valueOf(lastScore), xPosition, yPosition, Graphics.HCENTER | Graphics.TOP);
        } else {
            yPosition += fontHeight;
        }

        yPosition += fontHeight + fontHeight / 2;
        String extraScore = this.extraScore != null ? this.extraScore : "Fetching results...";
        if (!extraScore.equals("")) {
            int start = 0;
            int end = extraScore.indexOf('\n');
            while (end != -1) {
                g.drawString(extraScore.substring(start, end), xPosition, yPosition, Graphics.HCENTER | Graphics.TOP);
                yPosition += fontHeight;
                start = end + 1;
                end = extraScore.indexOf('\n', start);
            }
            g.drawString(extraScore.substring(start), xPosition, yPosition, Graphics.HCENTER | Graphics.TOP);
        }
    }

    protected void keyPressed(int keyCode) {
        switch (keyCode) {
            case Canvas.UP:
            case Canvas.KEY_NUM2:
            case -1:
                lastDirection = Point.UP;
                break;
            case Canvas.DOWN:
            case Canvas.KEY_NUM8:
            case -2:
                lastDirection = Point.DOWN;
                break;
            case Canvas.LEFT:
            case Canvas.KEY_NUM4:
            case -3:
                lastDirection = Point.LEFT;
                break;
            case Canvas.RIGHT:
            case Canvas.KEY_NUM6:
            case -4:
                lastDirection = Point.RIGHT;
                break;
        }
        if (gameLoop == null) {
            startGame();
        }
    }

    public void run() {
        try {
            repaint();
            while (true) {
                try {
                    Thread.sleep(world.getStepDelay());
                } catch (InterruptedException e) {
                    System.err.println(e);
                }

                if (!isShown()) continue;

                byte newDirection = lastDirection;
                byte currentDirection = world.getBody().getHeadSegment().direction;
                if (newDirection == Point.invertDirection(currentDirection)) {
                    newDirection = currentDirection;
                }
                movesStream.write(newDirection);
                if (!world.advance(newDirection) || world.getEatenFruits() >= NEEDED_FRUITS) {
                    lastScore = world.getEatenFruits();
                    highScore = Math.max(highScore, lastScore);
                    return;
                }

                repaint();
            }
        } finally {
            finishGame();
        }
    }

    private void startGame() {
        if (gameLoop != null) {
            // Probably still fetching the result.
            return;
        }

        world = new UzhWorld(secretCode, lastDirection);
        movesStream = new ByteArrayOutputStream();
        movesStream.write(lastDirection);
        extraScore = null;
        gameLoop = new Thread(this);
        gameLoop.start();
    }

    private void finishGame() {
        world = null;
        extraScore = "Fetching...";
        repaint();
        try {
            String url = "http://q.2024.ugractf.ru:9276/scores/?secret=" + secretCode;
            HttpConnection conn = (HttpConnection) Connector.open(url);
            try {
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/octet-stream");
                OutputStream outputStream = conn.openOutputStream();
                outputStream.write(movesStream.toByteArray());
                outputStream.close();
                int response_code = conn.getResponseCode();
                if (response_code != 200) {
                    extraScore = "Error " + response_code + ": " + conn.getResponseMessage();
                } else {
                    InputStream inputStream = conn.openInputStream();
                    ByteArrayOutputStream result = new ByteArrayOutputStream();
                    byte[] buffer = new byte[128];
                    for (int length; (length = inputStream.read(buffer)) != -1; ) {
                        result.write(buffer, 0, length);
                    }
                    inputStream.close();
                    extraScore = result.toString();
                }
            } finally {
                conn.close();
            }
        } catch (IOException e) {
            extraScore = e.toString();
        }
        repaint();
        gameLoop = null;
    }
}
