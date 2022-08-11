package org.ugra.uzh;

public class UzhBody {

    public class Segment {

        public Point head;
        public byte direction;
        public byte length;
        public Segment next;

        public Segment(Point head, byte direction, byte length) {
            this.head = head;
            this.direction = direction;
            this.length = length;
        }

        public Segment(Point head, byte direction) {
            this(head, direction, (byte)1);
        }

        public Point getTail() {
            Point tail = new Point(head);
            tail.advance((byte) -direction, length);
            return tail;
        }

        public boolean intersects(Point point) {
            switch (direction) {
                case Point.LEFT:
                    return point.y == head.y && point.x >= head.x && point.x <= head.x + length;
                case Point.RIGHT:
                    return point.y == head.y && point.x <= head.x && point.x >= head.x - length;
                case Point.DOWN:
                    return point.x == head.x && point.y >= head.y && point.y <= head.y + length;
                case Point.UP:
                    return point.x == head.x && point.y <= head.y && point.y >= head.y - length;
                default:
                    throw new RuntimeException("Invalid direction");
            }
        }

        public String toString() {
            return "{head=" + head.toString() + "; direction=" + Point.directionToString(direction) + "; length=" + String.valueOf(length) + "}";
        }
    }
    private Segment headSegment;
    private Segment tailSegment;
    private byte segmentsCount = 1;

    public UzhBody(Point origin, byte direction) {
        this(origin, direction, (byte)1);
    }

    public UzhBody(Point origin, byte direction, byte length) {
        headSegment = tailSegment = new Segment(origin, direction, length);
    }

    public Segment getHeadSegment() {
        return headSegment;
    }

    public Segment getTailSegment() {
        return tailSegment;
    }

    public byte getSegmentsCount() {
        return segmentsCount;
    }

    public void advanceHead(byte direction) {
        if (direction == headSegment.direction) {
            headSegment.head.advance(direction, (byte) 1);
            headSegment.length++;
        } else {
            Point newHead = new Point(headSegment.head);
            newHead.advance(direction, (byte) 1);
            Segment newHeadSegment = new Segment(newHead, direction);
            headSegment.next = newHeadSegment;
            headSegment = newHeadSegment;
            segmentsCount++;
        }
    }

    public void shrinkTail() {
        if (tailSegment.length == 1) {
            tailSegment = tailSegment.next;
            segmentsCount--;
        } else {
            tailSegment.length--;
        }
    }

    public boolean headIntersects() {
        Point head = headSegment.head;
        Segment segment = tailSegment;
        for (byte i = 0; i < segmentsCount - 3; i++) {
            if (segment.intersects(head)) {
                return true;
            }
            segment = segment.next;
        }
        return false;
    }

    public boolean pointIntersects(Point point) {
        Segment segment = tailSegment;
        do {
            if (segment.intersects(point)) {
                return true;
            }
            segment = segment.next;
        } while (segment != null);
        return false;
    }
}
