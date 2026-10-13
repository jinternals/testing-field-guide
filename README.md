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

`docs/` holds the guide as a PDF and as the one-file HTML it is printed from
(`docs/Testing-Field-Guide.html`, fonts and images inlined; open it in a browser). CI rebuilds both on
every push to `main` (the `guide` job): it collects the run's logs, re-runs the hand-run examples
(`guide/runs/regenerate.sh`: PIT, coverage, load, parallel, CPD), regenerates the screenshots,
renders the pages and publishes only if every check passes: no layout overflow, WCAG AA contrast,
fonts embedded, every stated version matching the builds (`guide/check_versions.py`) and every
sentence that interprets an output matching the new output (`guide/claims.py`).

To change the text, edit the page builders in `guide/` (`ch*.py`, `style.css`) and push; the files
in `docs/` are outputs and are overwritten. Locally: `guide/assemble.sh`, then in `guide/java`
`bash regenerate.sh`, then in `guide/` run `python3 shots.py`, `python3 build.py` and `python3 render.py`.
On Linux, install `guide/fonts.conf` into `/etc/fonts/conf.d/` first, as CI does: with screen font
settings (hinting, RGB subpixel) code blocks lay out wider and the layout check fails.
