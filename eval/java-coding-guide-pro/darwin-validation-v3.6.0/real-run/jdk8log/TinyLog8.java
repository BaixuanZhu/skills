import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
public class TinyLog8 {
    public static void main(String[] args) {
        Logger log = LoggerFactory.getLogger(TinyLog8.class);
        log.info("jdk8 combo ok {}", "slf4j-1.7.36+logback-1.2.13");
    }
}
