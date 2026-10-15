import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.data.*;
import java.io.*;
import java.util.*;

public class Task2_DumpStrings extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String out = getScriptArgs().length > 0 ? getScriptArgs()[0] : "work/strings.tsv";
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        int n = 0;
        try (PrintWriter w = new PrintWriter(new OutputStreamWriter(new FileOutputStream(out), "UTF-8"))) {
            DataIterator it = currentProgram.getListing().getDefinedData(true);
            while (it.hasNext()) {
                Data d = it.next();
                if (!(d.getValue() instanceof String)) continue;
                DataType dt = d.getDataType();
                String tn = dt.getName().toLowerCase();
                if (!tn.contains("string") && !tn.contains("unicode")) continue;
                String v = (String) d.getValue();
                StringBuilder xr = new StringBuilder();
                int c = 0;
                ReferenceIterator ri = rm.getReferencesTo(d.getAddress());
                while (ri.hasNext() && c < 6) {
                    Reference r = ri.next();
                    Function f = fm.getFunctionContaining(r.getFromAddress());
                    xr.append(f != null ? f.getName() + "@" + f.getEntryPoint() : "-").append(':').append(r.getFromAddress()).append(';');
                    c++;
                }
                w.println(d.getAddress() + "\t" + tn + "\t" + d.getLength() + "\t" + xr + "\t" + v.replace("\\", "\\\\").replace("\n", "\n").replace("\r", "\r").replace("\t", "\t"));
                n++;
            }
        }
        println("strings=" + n + " -> " + out);
    }
}
