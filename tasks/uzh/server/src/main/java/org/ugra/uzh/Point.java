package org.ugra.uzh;

public class Point {
    public static final byte LEFT = -1;
    public static final byte RIGHT = 1;
    public static final byte UP = -2;
    public static final byte DOWN = 2;

    public byte x;
    public byte y;

    public Point(byte x, byte y) {
        this.x = x;
        this.y = y;
    }

    public Point(Point that) {
        this.x = that.x;
        this.y = that.y;
    }

    void advance(byte direction, byte amount) {
        switch (direction) {
            case LEFT:
                x -= amount;
                break;
            case RIGHT:
                x += amount;
                break;
            case DOWN:
                y -= amount;
                break;
            case UP:
                y += amount;
                break;
            default:
                throw new RuntimeException("Invalid direction");
        }
    }

    public boolean equals(Object that) {
        if (!(that instanceof Point)) {
            return false;
        }
        Point thatPoint = (Point) that;
        return x == thatPoint.x && y == thatPoint.y;
    }

    public String toString() {
        return "(" + String.valueOf(x) + ", " + String.valueOf(y) + ")";
    }

    public static String directionToString(byte direction) {
        switch (direction) {
            case Point.DOWN:
                return "DOWN";
            case Point.UP:
                return "UP";
            case Point.LEFT:
                return "LEFT";
            case Point.RIGHT:
                return "RIGHT";
            default:
                throw new RuntimeException("Invalid direction");
        }
    }

    public static byte invertDirection(byte direction) {
        return (byte)-direction;
    }
}
