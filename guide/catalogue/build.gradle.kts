// Gradle plugins the guide recommends but the example build doesn't apply.
// `./gradlew -p guide/catalogue help` resolves them from the plugin portal; Dependabot keeps them current.
plugins {
  id("com.github.spotbugs") version "6.5.13" apply false
  id("org.owasp.dependencycheck") version "13.0.0" apply false
  id("org.gradle.test-retry") version "1.6.6" apply false
  id("org.sonarqube") version "7.5.0.8588" apply false
}
