# Testing Field Guide — example project

Companion code for the [*Testing Field Guide*](docs/Testing-Field-Guide.pdf) (Java 21, JUnit 6, Mockito 5,
AssertJ, Testcontainers 2). The same project builds with Maven and Gradle.

| Command | What it runs |
|---|---|
| `mvn verify` / `./gradlew check` | unit tests in parallel **threads**, integration tests in parallel **JVMs** (one singleton Postgres container per JVM), merged coverage |
| `mvn pmd:cpd-check` / `./gradlew cpdCheck` | copy-paste detection including test code |
| `mvn test-compile pitest:mutationCoverage exec:java` / `./gradlew pitest findRedundantTests` | mutation testing, then tests that kill the same mutants |

Integration tests need Docker.

`spring/` is a separate Spring Boot 4.1 project (`cd spring && mvn verify`): slice tests, full-context tests against PostgreSQL and ArchUnit rules.
`extras/` covers legacy code, Kafka, e-mail (GreenMail), WireMock with retries, Pact contracts, Flyway migrations, Playwright, JUnit extensions, logs and metrics, and AWS (Moto, LocalStack) and Azure (Azurite) emulators. `spring-auth/` tests a secured API with a mock OAuth2 server. Run each with `mvn verify`.

## How the guide is built

The PDF in `docs/` is rebuilt by CI on every push to `main` (the `guide` job). It
collects this run's logs, re-runs the hand-run examples (`guide/runs/regenerate.sh`: PIT,
coverage, load, parallel, CPD), regenerates the screenshots, and renders the PDF. It is
only published if every check passes: no layout overflow, WCAG AA contrast, fonts embedded,
and `guide/claims.py` — every sentence that interprets an output is checked against the new output.
