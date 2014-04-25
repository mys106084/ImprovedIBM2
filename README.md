---------------------------------------------------------
1.更改 defaultdict, 4个count dictionaries直接加delta

2.利用 lambda: 修改defaultdict的默认值, 2个probability dictionaries （t，q）初始值即为 infinitesmol

3.更改 xrange, 提升循环效率

4.修改初始化 normalisation

---------------------------------------------------------
1. Null alginment probability
(1) 设置 null aglignment probability (在delta 计算过程中完全替代q, 仅保留t)
(2) 同时修改evaluation function


2. Dirichlet Prior



---------------------------------------------------------

add Null alignment probability and Dirichlet prior


1.Inputcorpus()

2.EM_IBM2()

    2.0 Initial E-step: normalise delta[(s,i,j)]

    2.1 M-step:

        2.1.1 UpdateCounts_IBM2()

        2.1.2 ComputeT()
        
        2.1.3 ComputeQ_IBM2() when s>=5, since there is no ComputeQ for IBM1
        
    2.2 E-step:
    
        2.2.1 ComputeDelta_IBM1 when s<5
              ComputeDelta_IBM2 when s>=5
              
3.Dev_IBM2()




