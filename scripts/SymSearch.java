import ghidra.app.script.GhidraScript;
import ghidra.program.model.symbol.*;
import java.util.regex.*;

public class SymSearch extends GhidraScript {
    @Override
    protected void run() throws Exception {
        Pattern p = Pattern.compile(getScriptArgs()[0].replace("~", "|"), Pattern.CASE_INSENSITIVE);
        int max = getScriptArgs().length > 1 ? Integer.parseInt(getScriptArgs()[1]) : 300, n = 0;
        SymbolIterator it = currentProgram.getSymbolTable().getAllSymbols(true);
        while (it.hasNext() && n < max) {
            Symbol s = it.next();
            String full = s.getName(true);
            if (p.matcher(full).find()) { println(s.getAddress() + " " + s.getSymbolType() + " " + full); n++; }
        }
    }
}
