#!/usr/bin/env python3
import collections
import apsw

"""
Edge notation and meaning: 

    A -> B 

A must be completed *before* B, i.e. B depends on A. This conventation
stays close the idea of a chain of blocks (A -> B -> C -> ...) and its
meaning w.r.t dependency.
    
    
Open block on account B
-----------------------

A(send block) "destination [account]" -> B(open block) "source [block]"
C(open block)                         -> B(open block) "representative [account]"
    
(B.account == account being opened; no dependency)

Example: 8F02D66117CAC96AD0C66DB2DD583F8452D1CCE979FAEA5C72E4937F33F4ADA4
(receive 7M XRB on Developer Fund account from Genesis account)

Open block for developer fund (xrb_1ipx847tk8o46pwxt5qjdbncjqcbwcc1rrmqnkztrfjy5k7z4imsrata9est)

{
    "type": "open",
    "source": "4270F4FB3A820FE81827065F967A9589DF5CA860443F812D21ECE964AC359E05",
    "representative": "xrb_1awsn43we17c1oshdru4azeqjz9wii41dy8npubm4rg11so7dx3jtqgoeahy",
    "account": "xrb_1ipx847tk8o46pwxt5qjdbncjqcbwcc1rrmqnkztrfjy5k7z4imsrata9est",
    "work": "12d10d44912c9085",
    "signature": "712DF7C4AF0BD92446EC64D3F61D54510A93A591A638DB9DE812D9CB1B0B47EDAD31E7B23ECF3FD8AB9A948162A0CB5C1B8AB29E0C672029F53135F6B933B804"
}


Send block on account A
-----------------------

A(?)                                  -> A(send block) "previous [block]"
A(send block) "destination [account]" -> B(receive block) "source [block]"
A(send block) "destination [account]" -> B(open block) 

Example: C1319915AF94196644762318084B22A3AED1F4260281D3DB58E04D6662959E43

Send 300000000 xrb from xrb_1ipx847tk8o46pwxt5qjdbncjqcbwcc1rrmqnkztrfjy5k7z4imsrata9est
                   to xrb_1w76dejea4z9yywhgw477tppf6y5ya8rnxeao1e4qd3yy67w8o71cts6pqzd

{
    "type": "send",
    "previous": "B6C468ED59789B7533DAAB4CCD1A3D71C7A367550F93A3B3AB5AD988E00BA5CC",
    "destination": "xrb_1w76dejea4z9yywhgw477tppf6y5ya8rnxeao1e4qd3yy67w8o71cts6pqzd",
    "balance": "047A63D4920ACDE4D2D99CC540000000",
    "work": "de85d4cf59145ab0",
    "signature": "F95E2A60344A5D63AC62A4B53067D4A96B3AB39EEB5D948F786703C441971CCEEC9224D1E9602CB1B4A1131C439322ECA06513AC80E163980396E2318738BC05"
}

Balance (previous block):   047A729F1A5291F763E06B4840000000
Balance (this block):       047A63D4920ACDE4D2D99CC540000000

>>> int('047A729F1A5291F763E06B4840000000',16) - int('047A63D4920ACDE4D2D99CC540000000',16)
300000000000000000000000000000000L



Receive block on account B
--------------------------

B(previous block)   -> B(receive block) "previous [block]"
A(send block)       -> B(receive block) "source [block]"
Optional:
    A(send block) "destination [account]" -> B(open block)

Example: EE14DE802A996D061D75C6F970C317A5D2871D86E3BEC3A067B4C13F65D2CBCC

Corresponding receive block from send example above.

{
    "type": "receive",
    "previous": "9D6087001AE6E6614096CFE502DCAFBEFDC1BDD50288FC19AB06BBBA6FF125C8",
    "source": "C1319915AF94196644762318084B22A3AED1F4260281D3DB58E04D6662959E43",
    "work": "6b83b4582c089df7",
    "signature": "0A887F607AAF2B60FE6DA5DEA9BF3D9E7BD8FA1DF918471052FC0CBECE6AF7BE861C668ADA79BA46D791DCEDA297BD1876DEA10D2069F332509ACFA43D1E2700"
}



Change block on account B
-------------------------

B(?)            -> B(change block) "previous [block]"
C(open block)   -> B(change block) "representative [account]"

Example: E4F6E1C784A2D516441A919CC4A620CAB6887319BCD186DC637FC5EDA233EF94

{
    "type": "change",
    "previous": "C1319915AF94196644762318084B22A3AED1F4260281D3DB58E04D6662959E43",
    "representative": "xrb_1stofnrxuz3cai7ze75o174bpm7scwj9jn3nxsn8ntzg784jf1gzn1jjdkou",
    "work": "5a267240b70a9f22",
    "signature": "0F36816875BAB31C46BCEE32D3E4A0C3C1B6ED9644CB070E45DFF215E7973E74C7825D9786B71BA397C99F241F63497473D7DF92EA63DD23C371D1271AABAF03"
}



Should A.destination depend on the open block of the account being sent to?
I guess not, as the account might not be opened yet. For example, the last send 
from the genesis account of the remaining funds to the burn account 
(ECCB8CB65CD3106EDA8CE9AA893FEAD497A91BCA903890CBD7A5C59F06AB9113) is never 
received, and the burn hasn't been opened. 
The burn account (xrb_1111111111111111111111111111111111111111111111111111hifc8npp)
is valid though, while the example from the RPC validate_account_number call
(xrb_3e3j5tkog48pnny9dmfzj1r16pg8t1e76dz5tmac6iq689wyjfpi00000000) is invalid.
So in case the send destination account is opened, the send should come
before the destination account's open block.
Same remark for setting a representative to a non-opened account.

Can you send to the account being sent from? Yes!
https://nano.org/en/explore/block/2D6A9F3B01D0BF5973D7482F314362F9BA59E9E8415989EF3D6F574BF73210A2
{
    "type": "send",
    "previous": "514D68178C9B54F03D7F5CABBFC8CEB9F80007BDB6F79E02D46A03132484029B",
    "destination": "xrb_3m8n5i1yprf19mjiqook36eirpyf7er5mabdfaneixtt8fygewn7z7w88sym",
    "balance": "0026B610ABD328978FD07ADA00000000",
    "work": "ef1e40d7cb893a56",
    "signature": "3FC763A6DC0A194F308BEE693F6FCA865A427557E3F993E1A236FF118951F7F4A04E0B2F441BAB63D5A1D34B1D1AD735CCB03036C78EF47277714FBBC1EA8409"
}


"""

MARK_UNVISITED = 0
MARK_TEMPORARY = 1
MARK_PERMANENT = 2

trace = False

def visit(L, status, nodes, n):
    
    global trace
    
    if n == 220451:
        trace = True
        
    if trace:
        print('visit %d' % n)

    if status[n] == MARK_PERMANENT:
        return
        
    if status[n] == MARK_TEMPORARY:
        print(nodes[n])
        raise ValueError('Not a DAG (%d is marked as temporary)' % n)
        
    status[n] = MARK_TEMPORARY
    
    for m in nodes[n]:
        # Edge from n -> m
        visit(L, status, nodes, m)
        
    status[n] = MARK_PERMANENT
    
    L.appendleft(n)
    
    
def topological_sort(nodes):
    
    """
    nodes: {<node>: [<target-node>, ...]}
    """
    
    # Check consistency
    for src, dsts in nodes.items():
        for dst in dsts:
            if dst not in nodes:
                print('Warning: nodes[%d] contains %d, which is not in nodes[]' % (src, dst))
        
    L = collections.deque()
    stack = []

    # 0 = unvisisted, 1 = visited, but children not all visited yet, 2 = node and all its reachable children visited 
    status = {}   
    for src in nodes.keys():
        status[src] = MARK_UNVISITED
        
    # Push the Genesis block
    stack.append(0)
    
    while True:
        
        n = stack.pop()
        
        global trace
        
        if n == 220451:
            trace = True
            
        if trace:
            print('visit %d' % n)

        if status[n] == MARK_PERMANENT:
            continue
            
        if status[n] == MARK_TEMPORARY:
            print(nodes[n])
            raise ValueError('Not a DAG (%d is marked as temporary)' % n)
            
        status[n] = MARK_TEMPORARY
        
        for m in nodes[n]:
            # Edge from n -> m
            stack.append(m)
            visit(L, status, nodes, m)
            
        status[n] = MARK_PERMANENT
        
        L.appendleft(n)
        
        
        
    visit(L, status, nodes, 0)
        
    return list(L)
    
    
def generate_dependencies():
    
    def add_edge(src, dst):
        if src not in nodes:
            nodes[src] = [dst]
        else:
            nodes[src].append(dst)
    
    db = apsw.Connection(sys.argv[1], flags=apsw.SQLITE_OPEN_READONLY)
    cur = db.cursor()
    
    cur.execute('select id, account from blocks where type=?', ('open',))
    
    global block_to_type
    block_to_type = {}

    account_to_open_block = {}
    for id, account in cur:
        account_to_open_block[account] = id
    
    # XXX include representative?
    cur.execute('select id, type, previous, next, source, destination, i.account from blocks b, block_info i where b.id=i.block')
    
    nodes = {}
    used_block_ids = set()
    
    for id, type, previous, next, source, destination, this_account in cur:
        
        if id in [220451, 212959]:
            print(id, type, previous, next, source, destination, this_account)
            
        block_to_type[id] = type
        used_block_ids.add(id)
        
        if type == 'open':
            if source is not None:
                # {other} source -> open {this}
                if source != this_account:
                    # Unless sending to same account    
                    add_edge(source, id)
            if previous is not None:
                # {other} previous -> open {this}
                add_edge(previous, id)
        
        elif type == 'send':
            assert destination is not None
            """
            # XXX we can't make an open block always come after the send
            # block whole transfer it receives, as the send may (indirectly) transfer
            # to the current account and therefore open block. In which case there would be a cycle.
            # E.g. cycle starting at 288611994071C94E9881958A29D678974EA26DDD3F75B7D069F8AF82B999FBA8
            # {this} send -> destination account open {other} 
            # Make sure send appears before destination account is opened
            if destination in account_to_open_block:
                if destination != this_account:
                    # Unless sending to same account
                    # XXX Sending to the same account is legal, see 2D6A9F3B01D0BF5973D7482F314362F9BA59E9E8415989EF3D6F574BF73210A2
                    add_edge(id, account_to_open_block[destination])
            """
            
            # {this} send -> receive {other}
            # Handled in receive
            
            # {other} previous -> send {this}
            add_edge(previous, id)
            
        elif type == 'receive':
            # {other} send -> receive {this}
            add_edge(source, id)
            
            # {other} previous -> receive {this}
            add_edge(previous, id)
            
        elif type == 'change':
            # XXX representative
            
            if previous is not None:
                # {other} previous -> change {this}
                add_edge(previous, id)
                
    for id in used_block_ids:
        if id not in nodes:
            nodes[id] = []
            
    return nodes
    
def _traverse(f, visited, current):
    
    if current in visited:
        return False
        
    visited.add(current)
    
    label = '%d\\n%s' % (current, block_to_type[current])
    f.write('%d [label="%s"];\n' % (current, label))
    
    cont = True
    
    for dst in nodes[current]:
        f.write('%d -> %d;\n' % (current, dst))
        cont = cont and _traverse(f, visited, dst)
    
    return cont
    
    
def traverse_dot(fname, n):
    with open(fname, 'wt') as f:
        f.write('digraph G {\n')
        _traverse(f, set(), n)
        f.write('}\n')
    
    
if __name__ == '__main__':
    
    import sys
    
    nodes = {
        'A': ['B', 'C', 'D'],
        'B': ['C'],
        'C': [],
        'D': ['B'],
    }
    
    print('Generating edges')
    nodes = generate_dependencies()

    print('Creating igraph graph')
    import igraph
        
    edges = []
    for src, dsts in nodes.items():
        for dst in dsts:
            edges.append((src, dst))

    nv = max(nodes.keys())+1
    g = igraph.Graph(directed=True)
    g.add_vertices(nv)
    g.add_edges(edges)
    print('is DAG?', g.is_dag())
    
    print('sorting')
    order = g.topological_sorting()
    doh
    #traverse_dot('t.dot', 220451)
    #doh
    
    #for i in [0, 1, 2, 3, 4]:
    #    print(i, nodes[i])
    #doh
    
                
    print(len(nodes))
    
    print('Sorting')
    order = topological_sort(nodes)
    