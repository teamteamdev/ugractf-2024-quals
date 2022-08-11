package org.ugra.uzh;

import java.util.Random;

public class UzhWorld {
    public static final byte CELLS_X = 40;
    public static final byte CELLS_Y = 30;
    public static final int FRUIT_STEP_DELAY_SCALE = 1000;
    public static final int FRUIT_STEP_DELAY_K = 3000;

    private Random random;
    private UzhBody body;
    private Point fruit;
    private boolean ateFruit = false;
    private int stepDelay = 400;
    private int eatenFruits = 0;
    
    public UzhWorld(long seed, byte direction) {
        random = new Random(seed);
        Point origin = new Point((byte) (CELLS_X / 2), (byte) (CELLS_Y / 2));
        body = new UzhBody(origin, direction, (byte)5);
        spawnFruit();
    }

    public UzhBody getBody() {
        return body;
    }

    public Point getFruit() {
        return fruit;
    }

    public int getStepDelay() {
        return stepDelay;
    }

    public int getEatenFruits() {
        return eatenFruits;
    }

    public boolean advance(byte direction) {
        body.advanceHead(direction);
        if (ateFruit) {
            ateFruit = false;
        } else {
            body.shrinkTail();
        }

        Point head = body.getHeadSegment().head;
        if (body.headIntersects() || head.x < 0 || head.y < 0 || head.x >= CELLS_X || head.y >= CELLS_Y) {
            return false;
        }

        if (fruit.equals(body.getHeadSegment().head)) {
            ateFruit = true;
            spawnFruit();
            stepDelay = stepDelay * FRUIT_STEP_DELAY_SCALE / FRUIT_STEP_DELAY_K;
            eatenFruits++;
        }

        return true;
    }

    private void spawnFruit() {
        do {
            fruit = new Point(
                    (byte) (Math.abs(random.nextInt()) % CELLS_X),
                    (byte) (Math.abs(random.nextInt()) % CELLS_Y));
        } while (body.pointIntersects(fruit));
    }
}
