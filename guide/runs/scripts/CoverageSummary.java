package shop;

import java.io.File;
import java.util.*;
import org.jacoco.core.analysis.*;
import org.jacoco.core.tools.ExecFileLoader;
import org.jacoco.report.*;
import org.jacoco.report.html.HTMLFormatter;

/** Prints line/branch coverage per class for one or more .exec files and writes an HTML report. */
public class CoverageSummary {
  public static void main(String[] args) throws Exception {
    String classes = args[0], sources = args[1], htmlDir = args[2];
    var loader = new ExecFileLoader();
    for (int i = 3; i < args.length; i++) loader.load(new File(args[i]));
    var builder = new CoverageBuilder();
    new Analyzer(loader.getExecutionDataStore(), builder).analyzeAll(new File(classes));
    var bundle = builder.getBundle("shop");

    System.out.printf("%-26s %15s %15s%n", "class", "lines", "branches");
    List<IClassCoverage> sorted = new ArrayList<>(builder.getClasses());
    sorted.sort(Comparator.comparing(IClassCoverage::getName));
    for (IClassCoverage c : sorted) {
      if (c.getLineCounter().getTotalCount() == 0) continue;
      System.out.printf("%-26s %15s %15s%n", c.getName().replace("shop/", ""),
          fmt(c.getLineCounter()), fmt(c.getBranchCounter()));
    }
    System.out.printf("%-26s %15s %15s%n", "TOTAL",
        fmt(bundle.getLineCounter()), fmt(bundle.getBranchCounter()));

    var html = new HTMLFormatter().createVisitor(new FileMultiReportOutput(new File(htmlDir)));
    html.visitInfo(loader.getSessionInfoStore().getInfos(), loader.getExecutionDataStore().getContents());
    html.visitBundle(bundle, new DirectorySourceFileLocator(new File(sources), "utf-8", 2));
    html.visitEnd();
  }
  static String fmt(ICounter c) {
    if (c.getTotalCount() == 0) return "n/a";
    return String.format("%d/%d %3.0f%%", c.getCoveredCount(), c.getTotalCount(),
        100.0 * c.getCoveredRatio());
  }
}
