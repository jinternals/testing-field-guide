# Testing Field Guide — example project

Companion code for the [*Testing Field Guide*](docs/Testing-Field-Guide.pdf) (Java 21, JUnit 6, Mockito 5,
AssertJ, Testcontainers 2). The same project builds with Maven and Gradle.

| Command | What it runs |
|---|---|
| `mvn verify` / `./gradlew check` | unit tests in parallel **threads**, integration tests in parallel **JVMs** (one singleton Postgres container per JVM), merged coverage |
| `mvn pmd:cpd-check` / `./gradlew cpdCheck` | copy-paste detection including test code |
| `mvn test-compile pitest:mutationCoverage exec:java` / `./gradlew pitest findRedundantTests` | mutation testing, then tests that kill the same mutants |

Integration tests need Docker.

`spring/` is a separate Spring Boot 4.1 project (`cd spring && mvn verify`): slice tests and full-context tests against PostgreSQL.
`extras/` covers legacy code, Kafka, JUnit extensions, logs and metrics, and AWS (Moto, LocalStack) and Azure (Azurite) emulators. `spring-auth/` tests a secured API with a mock OAuth2 server. Run each with `mvn verify`.
