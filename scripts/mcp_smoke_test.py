import asyncio, sys, os, json
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRV = StdioServerParameters(command=sys.executable, args=[os.path.join(ROOT, 'dm12_mcp', 'server.py')], cwd=ROOT)


def payload(res):
    sc = getattr(res, 'structured_content', None) or getattr(res, 'structuredContent', None)
    if sc:
        return sc
    return json.loads(res.content[0].text)


async def main():
    async with Client(SRV) as c:
        tools = await c.list_tools()
        print('outils :', [t.name for t in tools.tools])
        st = payload(await c.call_tool('dm12_status', {}))
        print('status :', st['connected'], st['identity_reply'])
        rp = payload(await c.call_tool('dm12_read_patch', {}))
        print('patch courant :', repr(rp['name']), '| fx :', [(f['slot'], f['type']) for f in rp['fx']])
        dr = payload(await c.call_tool('dm12_apply_changes', {'changes': {'vcf.cutoff': 120}, 'dry_run': True}))
        print('dry-run : ecrit =', dr['written'], '| raison =', dr['reason'], '| octets =', dr['changed_bytes'])
        nc = payload(await c.call_tool('dm12_apply_changes', {'changes': {'porta.time': 5}, 'dry_run': False}))
        print('sans confirm : ecrit =', nc['written'], '|', nc['reason'])
        rk = payload(await c.call_tool('dm12_apply_changes', {'changes': {'vcf.resonance': 250}, 'dry_run': False, 'confirm': 'EDIT_BUFFER_ONLY'}))
        print('risque : ecrit =', rk['written'], '|', rk['risky_blocked'])
        cur = rp['params']['porta.time']
        newv = cur + 3 if cur < 250 else cur - 3
        wr = payload(await c.call_tool('dm12_apply_changes', {'changes': {'porta.time': newv}, 'dry_run': False, 'confirm': 'EDIT_BUFFER_ONLY'}))
        print('ecriture neutre : ecrit =', wr.get('written'), '| relecture identique =', wr.get('readback_identical'), '| sauvegarde =', wr.get('backup'))
        rs = payload(await c.call_tool('dm12_restore_backup', {'filename': wr['backup'], 'confirm': 'EDIT_BUFFER_ONLY'}))
        print('restauration :', rs.get('restored'), '| relecture identique =', rs.get('readback_identical'))
        back = payload(await c.call_tool('dm12_read_patch', {}))
        print('etat final = etat initial :', back['raw_hex'] == rp['raw_hex'])

asyncio.run(main())
