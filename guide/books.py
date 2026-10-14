"""File names and PDF metadata for each book built from this folder."""
import sys

BOOKS = {
    "guide": dict(html="guide.html", outline="outline.txt", raw="raw.pdf", pdf="Testing-Field-Guide.pdf",
                  title="Testing Java Applications — Field Guide",
                  subject="Unit, integration, API, end-to-end, performance and security testing in Java with JUnit 6, Mockito and AssertJ",
                  keywords="Java, testing, JUnit 6, Mockito, AssertJ, TDD, mutation testing, Testcontainers"),
    "deep": dict(html="deep.html", outline="deep-outline.txt", raw="raw-deep.pdf", pdf="Java-Performance-Deep-Dives.pdf",
                 title="Java Performance Deep Dives — a companion to the Testing Field Guide",
                 subject="TCP, timeouts, pools, latency measurement, JIT, GC, virtual threads, containers and the Java Memory Model, with measured experiments",
                 keywords="Java, TCP_NODELAY, Nagle, delayed ACK, TIME_WAIT, timeouts, Little's Law, coordinated omission, JIT, JMH, GC, ZGC, virtual threads, containers, Java Memory Model, jcstress"),
}


def book():
    """The book named on the command line (default: the main guide)."""
    name = sys.argv[1] if len(sys.argv) > 1 else "guide"
    return BOOKS[name]
