import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;

public class Task1_ProgramInfo extends GhidraScript {
    @Override
    protected void run() throws Exception {
        Program p = currentProgram;
        println("name=" + p.getName());
        println("format=" + p.getExecutableFormat());
        println("language=" + p.getLanguageID() + " compiler=" + p.getCompilerSpec().getCompilerSpecID());
        println("imageBase=" + p.getImageBase());
        println("functions=" + p.getFunctionManager().getFunctionCount());
        println("symbols=" + p.getSymbolTable().getNumSymbols());
        println("dataTypes=" + p.getDataTypeManager().getDataTypeCount(true));
        int named = 0, dflt = 0;
        for (Function f : p.getFunctionManager().getFunctions(true)) {
            if (f.getName().startsWith("FUN_")) dflt++; else named++;
        }
        println("functions_named=" + named + " functions_FUN_=" + dflt);
        for (MemoryBlock b : p.getMemory().getBlocks())
            println(String.format("block %-10s %s-%s size=0x%x init=%b perms=%s%s%s", b.getName(), b.getStart(), b.getEnd(), b.getSize(), b.isInitialized(),
                b.isRead()?"r":"-", b.isWrite()?"w":"-", b.isExecute()?"x":"-"));
        println("md5=" + p.getExecutableMD5());
        println("sha256=" + p.getExecutableSHA256());
        println("analyzed=" + p.getOptions("Program Information").getBoolean("Analyzed", false));
        for (String k : p.getOptions("Program Information").getOptionNames())
            if (k.contains("Compiler") || k.contains("PDB") || k.contains("RTTI") || k.contains("Version")) println("opt " + k + "=" + p.getOptions("Program Information").getValueAsString(k));
    }
}
