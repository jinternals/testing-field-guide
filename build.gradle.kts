plugins {
  java
  jacoco
  id("info.solidsoft.pitest") version "1.19.0"
  id("de.aaschmid.cpd") version "3.5"
}

java { toolchain { languageVersion = JavaLanguageVersion.of(21) } }
repositories { mavenCentral() }

sourceSets {
  create("integrationTest") {
    java.srcDir("src/it/java")
    compileClasspath += sourceSets.main.get().output
    runtimeClasspath += sourceSets.main.get().output
  }
  create("tools") { java.srcDir("src/tools") }
}
val integrationTestImplementation by configurations.getting {
  extendsFrom(configurations.testImplementation.get())
}
val integrationTestRuntimeOnly by configurations.getting {
  extendsFrom(configurations.testRuntimeOnly.get())
}
val mockitoAgent = configurations.create("mockitoAgent")

dependencies {
  testImplementation(platform("org.junit:junit-bom:6.1.3"))
  testImplementation("org.junit.jupiter:junit-jupiter")
  testRuntimeOnly("org.junit.platform:junit-platform-launcher")
  testImplementation("org.mockito:mockito-junit-jupiter:5.24.0")
  testImplementation("org.assertj:assertj-core:3.27.7")
  mockitoAgent("org.mockito:mockito-core:5.24.0") { isTransitive = false }
  integrationTestImplementation(
      "org.testcontainers:testcontainers-postgresql:2.0.5")
  integrationTestRuntimeOnly("org.postgresql:postgresql:42.7.14")
}

// UNIT tests: one JVM, many threads
tasks.test {
  useJUnitPlatform()
  jvmArgs("-javaagent:${mockitoAgent.asPath}", "-Xshare:off")
  systemProperty("junit.jupiter.execution.parallel.enabled", "true")
  systemProperty("junit.jupiter.execution.parallel.mode.default",
                 "concurrent")
  systemProperty("junit.jupiter.execution.parallel.mode.classes.default",
                 "concurrent")
}

// INTEGRATION tests: many JVMs, one singleton container each
val integrationTest = tasks.register<Test>("integrationTest") {
  description = "Runs *IT classes in parallel JVMs"
  group = "verification"
  testClassesDirs = sourceSets["integrationTest"].output.classesDirs
  classpath = sourceSets["integrationTest"].runtimeClasspath
  useJUnitPlatform()
  maxParallelForks = 2
  shouldRunAfter(tasks.test)
  testLogging { showStandardStreams = true }
}
tasks.check { dependsOn(integrationTest) }

// coverage of unit + integration tests in one report
tasks.jacocoTestReport {
  executionData(tasks.test.get(), integrationTest.get())
  dependsOn(tasks.test, integrationTest)
}

pitest {
  pitestVersion = "1.30.0"
  junit5PluginVersion = "1.2.3"
  targetClasses = setOf("shop.*")
  targetTests = setOf("shop.*Test")
  fullMutationMatrix = true
  outputFormats = setOf("XML", "HTML")
  timestampedReports = false
  jvmArgs = listOf("-XX:+EnableDynamicAgentLoading")
}

cpd {
  toolVersion = "7.17.0"
  minimumTokenCount = 25
}
tasks.cpdCheck {
  reports { text.required = true }
}

tasks.register<JavaExec>("findRedundantTests") {
  group = "verification"
  classpath = sourceSets["tools"].runtimeClasspath
  mainClass = "shop.RedundantTests"
  args("build/reports/pitest/mutations.xml")   // from the pitest task
  jvmArgs("-Dstdout.encoding=UTF-8")
}
