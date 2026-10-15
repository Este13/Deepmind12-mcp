import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class BindingClasses extends GhidraScript {
    @Override
    protected void run() throws Exception {
        Set<Function> fs = new TreeSet<>((a, b) -> a.getEntryPoint().compareTo(b.getEntryPoint()));
        for (String a : getScriptArgs())
            for (Reference r : currentProgram.getReferenceManager().getReferencesTo(toAddr(a)))
                if (r.getReferenceType().isCall()) {
                    Function f = currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
                    if (f != null) fs.add(f);
                }
        for (Function f : fs) {
            String cls = "?";
            InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
            outer:
            while (it.hasNext()) {
                Instruction in = it.next();
                for (Reference rr : in.getReferencesFrom()) {
                    Symbol s = currentProgram.getSymbolTable().getPrimarySymbol(rr.getToAddress());
                    if (s != null && s.getName(true).endsWith("::vftable")) { cls = s.getName(true).replace("::vftable", ""); break outer; }
                }
            }
            println("fn " + f.getEntryPoint() + " class=" + cls);
        }
    }
}
