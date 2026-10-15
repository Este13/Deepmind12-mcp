import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import java.io.*;

public class DecompRange extends GhidraScript {
    @Override
    protected void run() throws Exception {
        long lo = toAddr(getScriptArgs()[0]).getOffset(), hi = toAddr(getScriptArgs()[1]).getOffset();
        new File("work/decomp").mkdirs();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        int n = 0;
        for (Function f : currentProgram.getFunctionManager().getFunctions(toAddr(getScriptArgs()[0]), true)) {
            if (f.getEntryPoint().getOffset() >= hi) break;
            DecompileResults r = di.decompileFunction(f, 60, monitor);
            String c = r.decompileCompleted() ? r.getDecompiledFunction().getC() : "// failed";
            try (PrintWriter w = new PrintWriter("work/decomp/" + f.getEntryPoint() + ".c")) { w.println("// " + f.getName() + " @" + f.getEntryPoint()); w.println(c); }
            n++;
        }
        println("decompiled " + n);
    }
}
