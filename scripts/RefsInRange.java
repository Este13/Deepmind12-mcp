import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;

public class RefsInRange extends GhidraScript {
    @Override
    protected void run() throws Exception {
        AddressSet as = new AddressSet(toAddr(getScriptArgs()[0]), toAddr(getScriptArgs()[1]).subtract(1));
        AddressIterator it = currentProgram.getReferenceManager().getReferenceDestinationIterator(as, true);
        int n = 0;
        while (it.hasNext()) {
            Address to = it.next();
            for (Reference r : currentProgram.getReferenceManager().getReferencesTo(to)) {
                Function f = currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
                println(to + " <- " + r.getFromAddress() + " " + r.getReferenceType() + " " + (f == null ? "-" : f.getName() + "@" + f.getEntryPoint()));
                n++;
            }
        }
        println("total=" + n);
    }
}
