import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class EffectCtors extends GhidraScript {
    @Override
    protected void run() throws Exception {
        Address target = toAddr(getScriptArgs()[0]);
        for (Reference r : currentProgram.getReferenceManager().getReferencesTo(target)) {
            if (!r.getReferenceType().isCall()) continue;
            Function f = currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
            String arr = "?";
            Instruction ins = currentProgram.getListing().getInstructionAt(r.getFromAddress());
            for (int i = 0; i < 60 && ins != null; i++) {
                ins = ins.getPrevious();
                if (ins == null) break;
                if (ins.getDefaultOperandRepresentation(0).equals("RDX") && ins.getReferencesFrom().length > 0) {
                    for (Reference rr : ins.getReferencesFrom()) arr = rr.getToAddress().toString();
                    break;
                }
            }
            String cls = "?";
            if (f != null) {
                InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
                while (it.hasNext()) {
                    Instruction in = it.next();
                    for (Reference rr : in.getReferencesFrom()) {
                        Symbol s = currentProgram.getSymbolTable().getPrimarySymbol(rr.getToAddress());
                        if (s != null && s.getName(true).endsWith("::vftable")) { cls = s.getName(true).replace("::vftable", ""); break; }
                    }
                    if (!cls.equals("?")) break;
                }
            }
            println("ctor " + (f == null ? "-" : f.getEntryPoint().toString()) + " class=" + cls + " descriptors=" + arr);
        }
    }
}
