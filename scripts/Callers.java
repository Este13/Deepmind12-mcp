import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.scalar.*;
import java.util.*;

public class Callers extends GhidraScript {
    @Override
    protected void run() throws Exception {
        Address target = toAddr(getScriptArgs()[0]);
        String regs = getScriptArgs().length > 1 ? getScriptArgs()[1] : "EDX,RDX,DX,DL";
        Set<String> rs = new HashSet<>(Arrays.asList(regs.split(",")));
        int n = 0;
        for (Reference r : currentProgram.getReferenceManager().getReferencesTo(target)) {
            if (!r.getReferenceType().isCall()) continue;
            Function f = currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
            Instruction ins = currentProgram.getListing().getInstructionAt(r.getFromAddress());
            String val = "?";
            for (int i = 0; i < 14 && ins != null; i++) {
                ins = ins.getPrevious();
                if (ins == null) break;
                if (ins.getFlowType().isJump() || ins.getFlowType().isCall() && i > 0 && false) break;
                if (ins.getNumOperands() >= 2 && ins.getMnemonicString().equals("MOV") || ins.getMnemonicString().equals("XOR")) {
                    String op0 = ins.getDefaultOperandRepresentation(0);
                    if (rs.contains(op0)) {
                        if (ins.getMnemonicString().equals("XOR")) { val = "0"; break; }
                        Scalar s = ins.getScalar(1);
                        val = s != null ? String.valueOf(s.getSignedValue()) : ins.getDefaultOperandRepresentation(1);
                        break;
                    }
                }
            }
            println(String.format("caller %s@%s call@%s arg=%s", f == null ? "-" : f.getName(), f == null ? "-" : f.getEntryPoint(), r.getFromAddress(), val));
            n++;
        }
        println("total calls=" + n);
    }
}
