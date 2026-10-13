"""Chapter 6: a team conventions page — defaults drawn from the guide, each linked to its page."""
from lib import *

C = CH["6"]
CHAP = "06 · Quality &amp; process"

R = lambda k: ref(k)

GROUPS = [
    ("Naming &amp; layout", [
        ("Unit test classes", "<code>OrderServiceTest</code> in <code>src/test/java</code>, same package as the class", R("ci")),
        ("Integration tests", "<code>OrderFlowIT</code> — run by Failsafe in <code>verify</code>; may need Docker", R("parallel")),
        ("Test names", "say the behaviour: <code>unknownOrderIs404</code>, not <code>testGet2</code>", R("pyramid")),
        ("Shape", "one behaviour per test; Arrange · Act · Assert with blank lines between", R("pyramid")),
    ]),
    ("Writing tests", [
        ("Assertions", "AssertJ everywhere; one logical assertion per test, <code>assertAll</code>/soft assertions for groups", R("assert")),
        ("Test doubles", "mock only the boundaries you own (gateway, repository, mailer); real value objects", R("doubles")),
        ("Mockito", "<code>MockitoExtension</code> (strict stubs); <code>BDDMockito</code> in given/when/then tests", R("mockito2")),
        ("Time &amp; async", "inject a <code>Clock</code>; no <code>Thread.sleep</code> — use Awaitility or latches", R("tricky")),
        ("Test data", "builders with defaults (<code>anOrder().withItems(2).build()</code>); unique IDs per test, so parallel runs never collide", R("parallel")),
    ]),
    ("Spring Boot", [
        ("Default level", "slices first (<code>@WebMvcTest</code>, <code>@DataJpaTest</code>); <code>@SpringBootTest</code> for a few flows", R("spring")),
        ("Transactions", "no <code>@Transactional</code> on <code>@SpringBootTest</code> tests; one committed-path test per repository", R("txtrap")),
        ("Database", "Testcontainers with the production database and version, schema from the same Flyway/Liquibase migrations — not H2 as a stand-in", R("spring")),
    ]),
    ("Build gates <span class='muted' style='font-weight:400'>(suggested numbers — tune them)</span>", [
        ("Speed", "main build under ~10 minutes; slow suites move to nightly", R("ci")),
        ("Coverage", "branch coverage on <em>new</em> code ≥ 80% (JaCoCo <code>check</code> or a Sonar gate)", R("itcov")),
        ("Mutation", "PIT on core modules in pull requests, threshold ≥ 80%; everything nightly", R("pitci")),
        ("Duplication", "CPD on test code too (<code>includeTests</code>); start at 50 tokens, lower once clean", R("plugins")),
        ("Parallelism", "unit tests in threads always; integration forks only after measuring", R("parallel")),
        ("Flaky tests", "quarantine within a day; fix or delete within the sprint; never retry until green", R("tricky")),
    ]),
]

rows = ""
for g, items in GROUPS:
    rows += f'<tr><td colspan="3" class="grp" style="color:{C};font-weight:700;padding-top:2mm">{g}</td></tr>'
    rows += "".join(f'<tr><td class="nm">{a}</td><td>{b}</td><td class="c">{c}</td></tr>' for a, b, c in items)

WHERE = [
    ("Every push", "unit tests, CPD, PMD, Checkstyle, SpotBugs", "minutes; fail fast"),
    ("Every pull request", "integration tests, coverage gate on new code, PIT on the changed module", "blocks the merge"),
    ("Nightly", "full PIT, end-to-end and performance suites, Dependency-Check, duplicate-test report", "trends and alerts, not gates"),
]

REVIEW = [
    ("Would it fail?", "If the behaviour broke, would this test go red? (PIT answers this for you.)"),
    ("Right level?", "Is it the lowest level that can catch the bug — unit before integration before end-to-end?"),
    ("Readable?", "Does the name state the expected behaviour, and does a failure message say what went wrong?"),
    ("Independent?", "No shared state, real time, sleeps or test order; safe to run in parallel."),
]

page("conventions", f'''
{sub(CHAP, "Team testing conventions — a starting point", C)}
<p class="lede-s">A guide lists options; a team needs decisions. These defaults come from the pages of this guide — each row links to the page that explains it. Copy them into your repository’s <code>CONTRIBUTING.md</code>, then change what doesn’t fit your team. The numbers are suggestions, not standards.</p>
<table class="tbl xs"><thead><tr><th style="width:24%">Topic</th><th>Our default</th><th class="c" style="width:9%">Why</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Where each check runs</h2>
{table(["When", "Checks", "Role"], WHERE, "xs")}
<h2>Four questions for every test in code review</h2>
<div class="four">{"".join(f'<div class="card"><b class="h">{a}</b>{b}</div>' for a, b in REVIEW)}</div>
''', chapter=CHAP, color=C)
