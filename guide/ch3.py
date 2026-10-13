from lib import *

C = CH["3"]

# ============================================================================
# CH3 · doubles
# ============================================================================
DOUBLES = [("dummy", "Fills a parameter list; never actually used.", "Nothing", "<code>dummyEmail</code> throws if touched"),
           ("stub", "Returns canned answers to calls.", "State of the SUT", "<code>alwaysApproves</code> payment gateway"),
           ("spy", "A stub that also records the calls it got.", "Behaviour, checked by you", "<code>SpyEmailSender.sentTo</code>"),
           ("mock", "Pre-programmed with expectations; the library checks them.", "Behaviour", "Mockito <code>verify(email).send(…)</code>"),
           ("fake", "A working, simplified implementation.", "State, realistically", "<code>InMemoryOrderRepository</code>")]
dbl_rows = "".join(f'<tr><td>{dbl(a)}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>' for a, b, c, d in DOUBLES)

page("doubles", f'''
{head("03", "Chapter three", "Test doubles &amp; Mockito", "A unit test shouldn’t send real e-mails or charge real cards. A <b>test double</b> stands in for a collaborator, like a stunt double for an actor. The five kinds come from Gerard Meszaros’s <em>xUnit Test Patterns</em> (2007).", C)}
<h2>The five test doubles</h2>
<table class="tbl xs"><thead><tr><th>Double</th><th>What it is</th><th>What you verify</th><th>In this guide</th></tr></thead><tbody>{dbl_rows}</tbody></table>
<div class="two top" style="grid-template-columns:1.45fr 1fr;margin-top:3mm;gap:3.5mm">
  {code(jfile("TestDoublesTest.java"), "TestDoublesTest.java — no library needed", cls="xs", right="✔ 3 / 3 passed")}
  <div>
    <h2 style="margin-top:0">State or behaviour?</h2>
    <div class="concept-card" style="--accent:{DB['fake']}"><div class="cc-h">State verification</div><p>Run the code, then look at the result: what was returned, or what is now stored in the fake. Survives refactoring well, because it doesn’t care <em>how</em> the result was reached.</p></div>
    <div style="height:2.4mm"></div>
    <div class="concept-card" style="--accent:{DB['mock']}"><div class="cc-h">Behaviour verification</div><p>Check which calls were made to collaborators: “an e-mail was sent to Meera”. Needed when the call <em>is</em> the result — sending, publishing, charging — and nothing observable is stored.</p></div>

  </div>
</div>

''', chapter="03 · Test doubles &amp; Mockito", color=C, bm="03 · Test doubles &amp; Mockito")

# ============================================================================
# CH3 · mockito
# ============================================================================
API = [("Create", "<code>mock(X.class)</code> · <code>@Mock</code> · <code>spy(obj)</code> · <code>@Spy</code> · <code>@Captor</code> · <code>@InjectMocks</code>"),
       ("Stub", "<code>when(m.call()).thenReturn(v)</code> · <code>.thenThrow(e)</code> · <code>.thenAnswer(inv -&gt; …)</code>"),
       ("Stub void / spies", "<code>doThrow(e).when(m).call()</code> · <code>doReturn(v).when(spy).call()</code> · <code>doNothing()</code>"),
       ("Verify", "<code>verify(m).call()</code> · <code>times(2)</code> · <code>never()</code> · <code>atLeastOnce()</code> · <code>timeout(100)</code> · <code>verifyNoInteractions(m)</code>"),
       ("Order", "<code>InOrder o = inOrder(a, b); o.verify(a).x(); o.verify(b).y();</code>"),
       ("Match", "<code>any()</code> · <code>anyString()</code> · <code>eq(v)</code> · <code>contains(s)</code> · <code>argThat(x -&gt; …)</code> · <code>isNull()</code>"),
       ("Capture", "<code>verify(m).save(captor.capture()); captor.getValue()</code>"),
       ("BDD style", "<code>given(m.call()).willReturn(v)</code> · <code>then(m).should().call()</code>")]
api = "".join(f'<tr><td class="nm">{a}</td><td>{b}</td></tr>' for a, b in API)

page("mockito", f'''
{sub("03 · Test doubles &amp; Mockito", "Mockito in practice", C)}
<p class="lede-s"><code>placeOrder</code> applies the discount, charges the card, saves the order and e-mails the customer. In the test the gateway, repository and mailer are mocks; the clock is fixed.</p>
<div class="two top" style="grid-template-columns:1.45fr 1fr;gap:3.5mm;margin-bottom:2.6mm">
  {code(jfile("OrderService.java", "  public Order placeOrder", "    return order;\n  }", test=False, dedent=2), "OrderService.java — under test", cls="xs")}
  {ticks(["Every collaborator arrives through the <b>constructor</b>, so a test can pass in doubles — no framework needed.",
          "Time comes from an injected <code>java.time.Clock</code>, so the timestamp is predictable.",
          "<code>placeOrder</code> has one happy path and two failure paths: no items, or a declined card."], C)}
</div>
<div class="two top" style="grid-template-columns:1.45fr 1fr;gap:3.5mm">
  {code(jfile("OrderServiceTest.java", end="contains(\"₹1140.00\"));\n  }"), "OrderServiceTest.java (first test)", cls="xs")}
  <div>
    {code(suite_tree("OrderServiceTest"), "real output", kind="out", cls="xs", right="4 / 4 passed")}
    {ticks(["<b>@ExtendWith(MockitoExtension.class)</b> creates the <code>@Mock</code> and <code>@Captor</code> fields before each test and checks for unused stubs after it.",
            "<b>thenAnswer</b> makes <code>save</code> return its argument, like a real repository.",
            "<b>ArgumentCaptor</b> grabs the saved <code>Order</code> so we can check its timestamp came from the fixed clock.",
            "<b>eq</b> and <b>contains</b> are matchers: one matcher means all arguments need one."], C)}
  </div>
</div>
<div class="three" style="margin-top:2.6mm">
  <div class="card"><b class="h">Constructor beats @InjectMocks</b><code>@InjectMocks</code> builds the object by constructor, setter or field injection — and fails <em>silently</em> if it can’t. Calling the constructor yourself is explicit and breaks loudly.</div>
  <div class="card"><b class="h">Defaults of a mock</b>An unstubbed mock returns empty values: <code>null</code>, <code>0</code>, <code>false</code>, empty collections and <code>Optional.empty()</code>. Void methods simply do nothing.</div>
  <div class="card"><b class="h">Stub less, verify less</b>Stub only what the code path needs and verify only calls that are the point of the test — the rest is noise that breaks on refactors.</div>
</div>
<div class="two top" style="margin-top:1.8mm">
  <div class="vs"><div class="vs-pair">
      <div class="vs-side"><b>Classicist</b><p>Use real objects where possible, doubles only for awkward ones (network, time, mail).</p></div>
      <div class="vs-mid">vs</div>
      <div class="vs-side"><b>Mockist</b><p>Replace every collaborator with a mock and verify the conversation between objects.</p></div>
    </div><div class="vs-rule">From Fowler’s <em>Mocks Aren’t Stubs</em> (2007). Most teams lean classicist.</div></div>
  <div>{note("Mockito’s <code>mock()</code> can be a stub, spy or mock depending on use — the library blurs Meszaros’s names. The five kinds still help you decide what to check.", "info")}</div>
</div>
''', chapter="03 · Test doubles &amp; Mockito", color=C)

RULES = [("Don’t mock what you don’t own", "Wrap a third-party client (Stripe, S3, an HTTP SDK) in your own small interface and mock <em>that</em>. Test the wrapper against the real thing in an integration test."),
         ("Don’t mock values", "Records, <code>Money</code>, <code>List</code>, <code>LocalDate</code>: just create real ones. Mocking them makes tests longer and hides bugs."),
         ("Matchers: all or nothing", "If one argument uses a matcher, every argument must: <code>eq(\"a\"), any()</code>, not <code>\"a\", any()</code> — Mockito throws <code>InvalidUseOfMatchersException</code>."),
         ("A mock returning a mock is a smell", "<code>when(a.getB().getC())</code> means the code reaches through objects. Pass what it needs directly."),
         ("Verify outcomes, not every call", "<code>verifyNoMoreInteractions</code> on every test makes harmless refactors fail. Verify the calls that matter."),
         ("Too many mocks", "Five or more mocks in one test usually means the class does too much. Split it, or test a bigger unit with fakes.")]
rules = "".join(f'<div class="card"><b class="h">{a}</b>{b}</div>' for a, b in RULES)

page("mockito2", f'''
{sub("03 · Test doubles &amp; Mockito", "Failure paths, call order &amp; the API", C)}
<div class="two top" style="grid-template-columns:1.45fr 1fr;gap:3.5mm">
  {code(jfile("OrderServiceTest.java", "  @Test\n  void declinedPayment", "inOrder.verify(email).send(any(), any(), any());\n  }", dedent=2), "OrderServiceTest.java — failure path and call order", cls="xs")}
  <div>
    <h2 style="margin-top:0">The API on one table</h2>
    <table class="tbl xs"><tbody>{api}</tbody></table>
  </div>
</div>
<h2>Given / when / then with BDDMockito</h2>
<div class="two top" style="grid-template-columns:1.45fr 1fr;gap:3.5mm">
  {code(jfile("OrderServiceBddTest.java", "  @Test"), "OrderServiceBddTest.java", cls="xs", right="✔ passes")}
  <div>
    <p class="small"><code>BDDMockito</code> renames the same calls so tests read like a specification: <code>given(…).willReturn(…)</code> instead of <code>when(…).thenReturn(…)</code>, and <code>then(mock).should()</code> instead of <code>verify(mock)</code>. Pick one style per code base: mixing them makes readers wonder whether they behave differently — they don’t.</p>
  </div>
</div>
<h2>Rules that keep mocks honest</h2>
<div class="three">{rules}</div>
''', chapter="03 · Test doubles &amp; Mockito", color=C)

# ============================================================================
# CH3 · pitfalls
# ============================================================================
AGENT = """<plugin>  <!-- defines ${org.mockito:mockito-core:jar} -->
  <artifactId>maven-dependency-plugin</artifactId>
  <executions>
    <execution><goals><goal>properties</goal></goals></execution>
  </executions>
</plugin>
<plugin>
  <artifactId>maven-surefire-plugin</artifactId>
  <configuration>
    <argLine>@{argLine} -javaagent:${org.mockito:mockito-core:jar}</argLine>
  </configuration>
</plugin>"""


page("mockpit", f'''
{sub("03 · Test doubles &amp; Mockito", "Spies, statics, errors &amp; pitfalls", C)}
<div class="two top" style="grid-template-columns:1.45fr 1fr;gap:3.5mm">
  {code(jfile("MockitoFeaturesTest.java"), "MockitoFeaturesTest.java", cls="xs", right="✔ 4 / 4 passed")}
  <div>
    <h2 style="margin-top:0">Reading Mockito’s errors</h2>
    {code(fail_block("f_wantedButNotInvoked"), "verify(payments).charge(any(), any());", kind="out", cls="xs wrap")}
    <div style="height:1.6mm"></div>
    {code(fail_block("e_argumentMismatch"), "verify(email).send(…, \"Total: ₹1200.00\");", kind="out", cls="xs wrap")}
    <div style="height:1.6mm"></div>
    {code(fail_block("d_unnecessaryStubbing"), "a when(…) the test never used", kind="out", cls="xs wrap")}
  </div>
</div>
<p class="small muted" style="margin-top:1.4mm"><b>Strictness:</b> <code>MockitoExtension</code> defaults to <code>STRICT_STUBS</code> — unused stubs fail the test. <code>WARN</code> only logs; <code>LENIENT</code> ignores them. Change it with <code>@MockitoSettings(strictness = …)</code> or per stub with <code>lenient().when(…)</code>. An unused <code>when(…)</code> is dead setup that misleads readers, so keep the default. The three messages above are real output from deliberately failing tests.</p>

<div class="two top" style="margin-top:2.6mm;grid-template-columns:1fr 1.45fr">
  <div>
    {note("Mockito 5’s default <b>inline mock maker</b> (final classes, <code>mockStatic</code>) attaches a Java agent at run time. JDK 21+ warns about that (JEP 451) and a future JDK may refuse it — load Mockito as an agent in the build instead. <code>@{argLine}</code> must already be defined (JaCoCo’s <code>prepare-agent</code> sets it; otherwise declare an empty <code>argLine</code> property).", "warn", "JDK 21+ warning")}
  </div>
  {code(AGENT, "pom.xml — Mockito as a -javaagent (from Mockito’s docs)", kind="xml", cls="xs")}
</div>
''', chapter="03 · Test doubles &amp; Mockito", color=C)
