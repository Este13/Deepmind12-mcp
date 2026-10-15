import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.util.*;

public class XrefDecompile extends GhidraScript {
    @Override
    protected void run() throws Exception {
        boolean decomp = true;
        Set<Function> funcs = new LinkedHashSet<>();
        for (String a : getScriptArgs()) {
            if (a.equals("-n")) { decomp = false; continue; }
            if (a.startsWith("f:")) { Function ff = currentProgram.getFunctionManager().getFunctionContaining(toAddr(a.substring(2))); if (ff != null) funcs.add(ff); continue; }
            Address ad = toAddr(a);
            println("== " + a);
            Data d = currentProgram.getListing().getDataContaining(ad);
            if (d != null) println("   data: " + d.getDataType().getName() + " @" + d.getAddress() + " " + d.getDefaultValueRepresentation());
            for (Reference r : currentProgram.getReferenceManager().getReferencesTo(ad)) {
                Function f = currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
                println("   ref from " + r.getFromAddress() + " " + r.getReferenceType() + " in " + (f == null ? "-" : f.getName() + "@" + f.getEntryPoint() + " size=" + f.getBody().getNumAddresses()));
                if (f != null) funcs.add(f);
            }
        }
        if (!decomp) return;
        new File("work/decomp").mkdirs();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (Function f : funcs) {
            DecompileResults r = di.decompileFunction(f, 120, monitor);
            String c = r.decompileCompleted() ? r.getDecompiledFunction().getC() : "// decompile failed: " + r.getErrorMessage();
            try (PrintWriter w = new PrintWriter("work/decomp/" + f.getEntryPoint() + ".c")) { w.println("// " + f.getName() + " @" + f.getEntryPoint()); w.println(c); }
            println("decompiled " + f.getName() + "@" + f.getEntryPoint() + " (" + c.length() + " chars)");
        }
    }
}
