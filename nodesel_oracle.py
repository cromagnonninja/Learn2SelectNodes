from pathlib import Path
from pyscipopt import Model, Nodesel, Eventhdlr
import pyscipopt
import argparse

class Default_Estimate(Nodesel):
    def nodeselect(self):
        node = self.model.executeNodeSel('estimate')
        return {"selnode": node}
    def nodecomp(self, node1, node2): 
        node = self.model.executeNodeComp('estimate', node1, node2)


class Default_BFS(Nodesel):
    def nodeselect(self):
        node = self.model.executeNodeSel('bfs')
        return {"selnode": node}

class Default_Breadth(Nodesel):
    def nodeselect(self):
        node = self.model.executeNodeSel('breadthfirst')
        return {"selnode": node}

class Default_DFS(Nodesel):
    def nodeselect(self):
        node = self.model.executeNodeSel('dfs')
        return {"selnode": node}

class Default_Hybrid(Nodesel):
    def nodeselect(self):
        node = self.model.executeNodeSel('hybridestim')
        return {"selnode": node}

class Default_UCT(Nodesel):
    def nodeselect(self):
        node = self.model.executeNodeSel('uct')
        return {"selnode": node}

class Default_Restart(Nodesel):
    def nodeselect(self):
        node = self.model.executeNodeSel('restartdfs')
        return {"selnode": node}


class Oracle(Nodesel):
    def __init__(self, solution_path): 
        self.opt_checked = {} 
        self.opt_nodes = {}
        self.feat = {'maxdepth':[]}
        self.optfeat = {'maxdepth':[]}
        self.optnodenumber = -1
        self.negate = True
        self.solution_path = solution_path
        
    def nodeinit(self): 
        self.feat['maxdepth'].append(self.model.getNBinVars() + self.model.getNintVars())
        self.optfeat['maxdepth'].append(self.model.getNBinVars() + self.model.getNintVars())
        self.opt_sol = self.model.readSolFile(self.solution_path)

    def nodeselect(self): 
        leaves, children, siblings = self.model.getOpenNodes()
        # print(type(leaves), type(children), type(siblings))
        self.optchild = -1
        for idx, child in enumerate(children):
            # print("loop activated")
            if child.getNumber() not in self.opt_checked: 
                parent = child.getParent()
                # root -> trivially optimal 
                if(parent.getDepth() > 0 and not self.opt_nodes[parent.getNumber()]): 
                    optimal = True   
                nbranchvars = child.getNParentBranchings()
                # print(nbranchvars)
                branchvars, branchbounds, boundtypes = child.getParentBranchings()
                optimal = True 
                for i in range(nbranchvars):
                    optval = self.model.getSolVal(self.opt_sol, branchvars[i])
                    # print(optval)
                    if boundtypes[i] == 0 and optval < branchbounds[i] or boundtypes[i] == 1 and optval > branchbounds[i]: 
                        optimal = False 
                self.opt_checked[child.getNumber()] = True
                self.opt_nodes[child.getNumber()] = optimal 
            
            if child.getNumber() in self.opt_nodes:
                self.optnodenumber = child.getNumber()
                self.optchild = idx          
                # print(self.optnodenumber)
                # print(self.optchild)

            #TODO: Lines 461 through to 503 of the nodesel_oracle.c file need to implemented here. 

        node = self.model.getBestNode()
        return {"selnode": node}
        
    def nodecomp(self, node1, node2): 
        isoptimal1 = self.opt_nodes[node1.getNumber()]
        isoptimal2 = self.opt_nodes[node2.getNumber()]
        if(isoptimal1):
            assert(not isoptimal2)
            return -1
        elif isoptimal2:
            return 1
        else:
            depth1 = node1.getDepth()
            depth2 = node2.getDepth()
            if (depth1 > depth2):
                return -1
            elif (depth1 < depth2):
                return 1
            else:
                lowerbound1 = node1.getLowerbound()
                lowerbound2 = node2.getLowerbound()
                if(self.model.isLT(lowerbound1, lowerbound2)):
                    return -1
                elif(self.model.isGT(lowerbound1, lowerbound2)):
                    return 1
                # Why check the same thing twice? What is the purpose/benefits?
                if lowerbound1 < lowerbound2:
                    return -1
                elif lowerbound1 > lowerbound2:
                    return 1
                else:
                    return 0


class OracleNodeSel(Nodesel):
    def __init__(self, solution_path): 
        self.opt_checked = {} 
        self.opt_nodes = {}
        self.feat = {'maxdepth':[]}
        self.optfeat = {'maxdepth':[]}
        self.optnodenumber = -1
        self.negate = True 
        self.solution_path = solution_path       

    def nodeinit(self): 
        self.feat['maxdepth'].append(self.model.getNBinVars() + self.model.getNintVars())
        self.optfeat['maxdepth'].append(self.model.getNBinVars() + self.model.getNintVars())
        self.opt_sol = self.model.readSolFile(self.solution_path)

    
    def nodeselect(self): 
        leaves, children, siblings = self.model.getOpenNodes()
        # print(type(leaves), type(children), type(siblings))
        self.optchild = -1
        for idx, child in enumerate(children):
            # print("loop activated")
            if child.getNumber() not in self.opt_checked: 
                parent = child.getParent()
                # root -> trivially optimal 
                if(parent.getDepth() > 0 and not self.opt_nodes[parent.getNumber()]): 
                    optimal = True   
                nbranchvars = child.getNParentBranchings()
                # print(nbranchvars)
                branchvars, branchbounds, boundtypes = child.getParentBranchings()
                optimal = True 
                for i in range(nbranchvars):
                    optval = self.model.getSolVal(self.opt_sol, branchvars[i])
                    # print(optval)
                    if boundtypes[i] == 0 and optval < branchbounds[i] or boundtypes[i] == 1 and optval > branchbounds[i]: 
                        optimal = False 
                self.opt_checked[child.getNumber()] = True
                self.opt_nodes[child.getNumber()] = optimal 
            
            if child.getNumber() in self.opt_nodes:
                self.optnodenumber = child.getNumber()
                self.optchild = idx

            #TODO: Lines 461 through to 503 of the nodesel_oracle.c file need to implemented here. 

        node = self.model.getBestNode()
        return {"selnode": node}


# loop over multiple problems 
parser = argparse.ArgumentParser(description='Solve a few MILPs')
parser.add_argument('method')
args = parser.parse_args()

list_files_indset = Path('/Users/work/Desktop/learn2branch/data/instances/indset/transfer_500_4/').glob("*.lp")
for problem_path in list_files_indset: 
    m = Model()
    m.readProblem(str(problem_path))
    if args.method == 'oracle': 
        m.includeNodesel(Oracle(str(problem_path) + '_solution.txt'), "oracle_nodesel", "", 1073741823, 536870911)
    if args.method == 'oracle_nodesel': 
        m.includeNodesel(OracleNodeSel(str(problem_path) + '_solution.txt'), "oracle_nodesel_only", "", 1073741823, 536870911)
    if args.method == 'estimate': 
        m.includeNodesel(Default_Estimate(), "scip_estimate", "", 1073741823, 536870911)
    if args.method == 'bfs': 
        m.includeNodesel(Default_BFS(), "scip_bfs", "", 1073741823, 536870911)
    if args.method == 'restartdfs': 
        m.includeNodesel(Default_Restart(), "scip_restart_dfs", "", 1073741823, 536870911)
    if args.method == 'uct': 
        m.includeNodesel(Default_UCT(), "scip_uct", "", 1073741823, 536870911)
    if args.method == 'breadth': 
        m.includeNodesel(Default_Breadth(), "scip_breadth", "", 1073741823, 536870911)
    if args.method == 'hybrid': 
        m.includeNodesel(Default_Hybrid(), "scip_hybrid_estimate", "", 1073741823, 536870911)
    if args.method == 'dfs': 
        m.includeNodesel(Default_DFS(), "scip_dfs", "", 1073741823, 536870911)    
    m.optimize()
    m.writeStatistics((str(problem_path) + "_" + str(args.method)).strip(".") + "_" + "stats.txt")
    m.freeProb()

# list_files_setcover = Path('/Users/work/Desktop/learn2branch/data/instances/setcover/transfer_500r_1000c_0.05d/').glob("*.lp")
# for problem_path in list_files_setcover: 
#     m = Model()
#     m.readProblem(str(problem_path))
#     if args.method == 'oracle': 
#         m.includeNodesel(Oracle(str(problem_path) + '_solution.txt'), "oracle_nodesel", "", 1073741823, 536870911)
#     if args.method == 'oracle_nodesel': 
#         m.includeNodesel(OracleNodeSel(str(problem_path) + '_solution.txt'), "oracle_nodesel_only", "", 1073741823, 536870911)
#     if args.method == 'default': 
#         m.includeNodesel(Default(), "default", "", 1073741823, 536870911)
#     m.optimize()
#     m.writeStatistics((str(problem_path) + "_" + str(args.method)).strip(".") + "_" + "stats.txt")
#     m.freeProb()
    

# list_files_bounded = Path('/Users/work/Desktop/Learn2SelectNodes/mik.data/bounded/').rglob('*.mps.gz')    # 90 bounded files
# for path in list_files_bounded:
#     m = Model()
#     m.readProblem(str(path))
#     if args.method == 'oracle': 
#         m.includeNodesel(Oracle(str(path) + '_solution.txt'), "oracle_nodesel", "", 1073741823, 536870911)
#     if args.method == 'oracle_nodesel': 
#         m.includeNodesel(OracleNodeSel(str(path) + '_solution.txt'), "oracle_nodesel_only", "", 1073741823, 536870911)
#     if args.method == 'estimate': 
#         m.includeNodesel(Default_Estimate(), "default", "", 1073741823, 536870911)
#     if args.method == 'default': 
#         m.includeNodesel(Default(), "default", "", 1073741823, 536870911)
   
#     m.optimize()
#     m.writeStatistics((str(problem_path) + "_" + str(args.method)).strip(".") + "_" + "stats.txt")
#     m.freeProb()