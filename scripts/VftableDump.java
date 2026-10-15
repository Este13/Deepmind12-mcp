import ghidra.app.script.GhidraScript;
import ghidra.program.model.symbol.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.io.*;
import java.util.regex.*;

public class VftableDump extends GhidraScript {
    @Override
    protected void run() throws Exception {
        Pattern p = Pattern.compile(getScriptArgs()[0].replace("~", "|"));
        try (PrintWriter w = new PrintWriter("work/vftables.tsv", "UTF-8")) {
            SymbolIterator it = currentProgram.getSymbolTable().getAllSymbols(true);
            while (it.hasNext()) {
                Symbol s = it.next();
                String n = s.getName(true);
                if (!n.endsWith("::vftable") || !p.matcher(n).find()) continue;
                Address a = s.getAddress();
                for (int i = 0; i < 80; i++) {
                    Address slot = a.add(8L * i);
                    if (i > 0 && currentProgram.getSymbolTable().getPrimarySymbol(slot) != null) break;
                    long v = currentProgram.getMemory().getLong(slot);
                    Address f = toAddr(v);
                    if (f == null || !currentProgram.getMemory().contains(f)) break;
                    Function fn = currentProgram.getFunctionManager().getFunctionAt(f);
                    if (fn == null) break;
                    w.println(n.replace("::vftable", "") + "\t" + a + "\t" + i + "\t" + f);
                }
            }
        }
    }
}
