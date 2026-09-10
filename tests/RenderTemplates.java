import freemarker.template.Configuration;
import freemarker.template.TemplateExceptionHandler;
import java.io.Reader;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Properties;

/** Render the real Polygon templates using Apache FreeMarker and fixture data. */
public final class RenderTemplates {
    public static void main(String[] args) throws Exception {
        Path templates = Path.of(args[0]);
        Path output = Path.of(args[1]);
        Properties fixture = new Properties();
        try (Reader reader = Files.newBufferedReader(output.resolve("fixture.properties"))) {
            fixture.load(reader);
        }

        Configuration configuration = new Configuration(Configuration.VERSION_2_3_34);
        configuration.setDirectoryForTemplateLoading(templates.toFile());
        configuration.setDefaultEncoding("UTF-8");
        configuration.setLocale(Locale.ROOT);
        configuration.setTemplateExceptionHandler(TemplateExceptionHandler.RETHROW_HANDLER);
        configuration.setLogTemplateExceptions(false);
        configuration.setWrapUncheckedExceptions(true);

        boolean contest = Boolean.parseBoolean(fixture.getProperty("contest", "false"));
        int count = Integer.parseInt(fixture.getProperty("count", "1"));
        List<Map<String, Object>> statements = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            String prefix = "problem." + i + ".";
            String directory = contest ? "problems/" + (char) ('A' + i) + "/" : "";
            Path problemDirectory = output.resolve(directory);
            Files.createDirectories(problemDirectory);
            Map<String, Object> problem = new HashMap<>();
            problem.put("name", fixture.getProperty(prefix + "name", "Smoke"));
            problem.put("inputFile", fixture.getProperty(prefix + "inputFile", "stdin"));
            problem.put("outputFile", fixture.getProperty(prefix + "outputFile", "stdout"));
            problem.put("timeLimit", 1000);
            problem.put("memoryLimit", 268435456);
            problem.put("legend", fixture.getProperty(prefix + "legend", "Find the sum of the values."));
            problem.put("input", "Read the values.");
            problem.put("output", "Print the result.");
            problem.put("notes", "ENDPROBLEM" + (char) ('A' + i));
            int samples = Integer.parseInt(fixture.getProperty(prefix + "samples", "1"));
            List<Map<String, String>> sampleTests = new ArrayList<>();
            for (int sample = 0; sample < samples; sample++) {
                sampleTests.add(Map.of("inputFile", "sample" + sample + ".in",
                                      "outputFile", "sample" + sample + ".ans"));
            }
            problem.put("sampleTests", sampleTests);
            Map<String, Object> model = new HashMap<>();
            model.put("problem", problem);
            model.put("language", fixture.getProperty("language", "chinese"));
            model.put("providedStatementsCommands", List.of());
            try (Writer writer = Files.newBufferedWriter(problemDirectory.resolve("statement.tex"), StandardCharsets.UTF_8)) {
                configuration.getTemplate("problem.tex").process(model, writer);
            }
            Map<String, Object> statement = new HashMap<>();
            statement.put("file", "statement.tex");
            if (contest) {
                statement.put("path", directory);
                statement.put("index", String.valueOf((char) ('A' + i)));
            }
            statements.add(statement);
        }

        Map<String, Object> document = new HashMap<>();
        document.put("contest", Map.of("name", "Template Regression", "date", "2026-09-10", "location", "Test Venue"));
        document.put("statements", statements);
        document.put("shortProblemTitle", false);
        try (Writer writer = Files.newBufferedWriter(output.resolve("document.tex"), StandardCharsets.UTF_8)) {
            configuration.getTemplate("statements.ftl").process(document, writer);
        }
    }
}
