## Conformal Off-Policy Evaluation in Markov Decision Processes

Daniele Foffano ∗ , Alessio Russo ∗ and Alexandre Proutiere

Abstract -Reinforcement Learning aims at identifying and evaluating efficient control policies from data. In many realworld applications, the learner is not allowed to experiment and cannot gather data in an online manner (this is the case when experimenting is expensive, risky or unethical). For such applications, the reward of a given policy (the target policy) must be estimated using historical data gathered under a different policy (the behavior policy). Most methods for this learning task, referred to as Off-Policy Evaluation (OPE), do not come with accuracy and certainty guarantees. We present a novel OPE method based on Conformal Prediction that outputs an interval containing the true reward of the target policy with a prescribed level of certainty. The main challenge in OPE stems from the distribution shift due to the discrepancies between the target and the behavior policies. We propose and empirically evaluate different ways to deal with this shift. Some of these methods yield conformalized intervals with reduced length compared to existing approaches, while maintaining the same certainty level.

## I. INTRODUCTION

In this work, we consider the problem of off-policy evaluation (OPE) in finite time-horizon Markov Decision Processes (MDPs). This problem is concerned with the task of learning the expected cumulative reward of a target policy from data gathered under a different behavior policy. In fact, OPE has attracted a lot of attention recently [10], [23], [19], [25], [5], [15] since it is particularly relevant in real-world scenarios where the learner is not allowed to experiment and deploy the target policy to infer its value. In these scenarios, testing a new policy in an online manner can be indeed too risky or unethical (e.g., in finance or healthcare).

The main challenge in OPE algorithms stems from the distribution shift of the target and behavior policies. To address this issue, researchers have developed various solutions, often based on Importance Sampling methods (refer to §II and to [29] for a recent survey). Lastly, while existing OPE algorithms sometimes enjoy asymptotic convergence properties, most of them do not come with accuracy and certainty guarantees [25], [26], [7].

To that aim, we are concerned with devising OPE estimators that enjoy non-asymptotic performance guarantees. We leverage techniques from Conformal Prediction (CP) [30], [28], [21], which, directly from the data, allow to build conformalized sets that provably includes the true value of the quantity to be estimated with a prescribed level of certainty. Furthermore, CP is a distribution-free method, thus circumventing the burden of estimating a model while providing non-asymptotic guarantees. Due to these desirable properties, CP has been applied with success in many fields, including medicine [14], [33], [16], aerospace engineering [32], finance [31] and safe motion planning [13].

∗ Equal contribution

Daniele Foffano, Alessio Russo and Alexandre Proutiere are in the Division of Decision and Control Systems of the EECS School at KTH Royal Institute of Technology, Stockholm, Sweden. {foffano,alessior,alepro}@kth.se

Nevertheless, standard CP assumes to be trained on i.i.d. data, and that at test time the data comes from the same distribution from which the training data was drawn (a.k.a. as distribution/covariates shift ). This latter assumption is violated in OPE problems, since the training data is gathered using a policy than is different from the target policy to be evaluated. A solution to address the distribution shift is to leverage the concept of weighted exchangeability [28], [12].

By exploiting the concept of weighted exchengeability, we study the conformalized OPE problem for Markov Decision Processes (MDPs). Our method builds on top of the technique described in [24], which introduces conformalized OPE for contextual bandit models (which can be seen as MDPs with i.i.d. states). Compared to [24], we have to handle additional difficulties, including the inherent dependence in the data (which consists of trajectories of a controlled Markov chain) and the statistical hardness of dealing with the distribution shift when the time horizon grows large.

Contribution-wise, we present and empirically evaluate CP algorithms that yield conformalized intervals with reduced length compared to existing approaches, while maintaining the same certainty level. These algorithms are based on the two following new components. (i) Asymmetric score functions: existing CP approaches use symmetric score functions and hence, for our problem, would output conformalized intervals centered on the value of the behavior policy. We introduce asymmetric score functions, so that the CP algorithm yields an interval that efficiently moves its center to follow the distribution shift. In turn, CP with asymmetric score functions results in intervals of smaller size. (ii) We propose methods to address the distribution shift in MDPs.

We finally illustrate the performance of our algorithms numerically on the classical inventory control problem [20]. The experiments demonstrate that indeed our algorithms achieve smaller interval lengths than existing approaches, while retaining the same certainty guarantees.

## II. RELATED WORK

A. Off-Policy Evaluation (OPE)

There are mainly three classes of OPE algorithms in the literature: Direct, Importance Sampling and Doubly Robust Methods. Direct Methods (DMs) learn a model of the system [10], [23] and then evaluate the policy against it. DMs can lead to biased estimators due to a mismatch between the model and the true system. Importance Sampling (IS) is a well-known method [19], [25], [5], [15] used to correct the distribution mismatch caused by the discrepancies between the target and the behavior policies by re-weighting the sampled rewards. Still, IS-based algorithms suffer from high variance in long-horizon problems. Doubly Robust (DR) methods combine DMs and IS to obtain more robust estimators [7], [6]. [15] introduce Marginalized Importance Sampling, reducing the variance by applying IS directly on the stationary statevisitation distribution.

The aforementioned approaches only provide an accurate point-wise estimate of the policy value, without quantifying its uncertainty. [1] derived confidence intervals (CIs) using the Central Limit Theorem. In [25], [9], the authors leveraged concentration inequalities to estimate good CIs, which, however, tend to be overly-conservative. For short-horizon problems, [26], [5] approximate CIs for OPE can also be found by means of bootstrapping. [22] derives a non-asymptotic CI using concentration bounds on a kernel-based Q-function.

In [8], the authors derive an asymptotic CI using Double Reinforcement Learning (DRL), also addressing the curse of the horizon. However, the DRL method might not converge in high-dimensional RL tasks, resulting in an asymptotically biased estimator. [3], [23] derive non-asymptotic and asymptotic CIs by approximating the value function with linear functions, but their approaches might lead to a biased estimator if the model assumption is incorrect. [7] derived a CI that involves solving a linear program, but they assume the observations to be i.i.d., whereas transitions are time-dependent in many RL problems.

## B. Conformal Prediction (CP)

CP is a frequentist technique to derive CIs with a specified coverage ( i.e. , confidence) and a finite number of i.i.d. samples (we refer the reader to [17] for a comprehensive list of CP-related papers). The advantage of CP with respect to other methods is that the provided coverage guarantees are distribution-free and non-asymptotic.

CP for off-policy evaluation has been recently applied to the contextual bandit setting [24], which, in contrast to our work, has no dynamics and no time-dependent data. To address the distribution shift, the authors in [24] use of the weighted exchangeability property, which was previously introduced in [28]. In [2], the authors apply CP to predict the expected value of MDPs trajectories. They consider an online setting where they do not have to deal with the distribution shift.

## III. PRELIMINARIES

## A. Off-policy evaluation in Markov Decision Processes

We consider finite-time horizon MDPs [20]. Such an MDP is defined by a tuple M = 〈X , A , T, q, p, H 〉 , where X and A are the (finite) state and action spaces, respectively. For all ( x, a ) ∈ X×A , T ( ·| x, a ) and q ( ·| x, a ) denote the distributions of the next state and of the instantaneous reward given that the current state is x and that the decision maker selects action a (for simplicity, we assume that the transition probabilities and the reward distributions are stationary; our results can be easily generalized to non-stationary dynamics and rewards). Finally, p ∈ ∆( S ) denotes the distribution of the initial state, and H the time horizon.

In off-policy evaluation, we gather data using a behavior policy π b , and we wish to estimate the value function of different policy π . Here again for simplicity, we consider stationary policies: both π b and π are mappings between the state space and the set ∆( A ) of distributions over actions. The value function of π maps the initial state x to the expected reward gathered under π when starting in x : V π H ( x ) = E π [ ∑ H t =1 r t | x 1 = x ] , where r t ∼ q ( ·| x t , a t ) , a t ∼ π ( ·| x t ) , and x t +1 ∼ T ( ·| x t , a t ) for t = 1 , . . . , H .

## B. Standard Conformal Prediction

Conformal Prediction (CP) is a method for distributionfree uncertainty quantification of learning methods, see e.g. [30], [18], [11]. To illustrate how CP works, we consider classical supervised learning tasks and restrict our attention to split CP where the pre-training and the calibration phases are conducted on different datasets. The learner starts with a pretrained model ˆ f : X → Y that maps inputs to predicted labels (this model may also consist of upper and lower estimated quantiles if the pre-training procedure corresponds to quantile regression). She also has i.i.d. calibration data D cal = { X i , Y i } n i =1 i.i.d. ∼ P X,Y . From ˆ f and D cal , CP constructs for each possible input x a subset ˆ C n ( x ) of possible labels. More precisely, the method proceeds as follows: (i) first a score function s : X × Y → R is constructed from the model ˆ f (e.g., it could be the residuals | y -ˆ f ( x ) | if Y ⊂ R ); (ii) the scores of the various calibration samples are computed V i = s ( X i , Y i ) , and (iii) the confidence set is built according to ˆ C n ( x ) = { y ∈ Y : s ( x, y ) ≤ η } , where η = Quantile 1 -α ( 1 n +1 (∑ n i =1 δ V i + δ {∞} ) ) . If ( X 1 , Y 1 ) , . . . , ( X n +1 , Y n +1 ) are exchangeable, this construction ensures coverage with certainty level 1 -α :

<!-- formula-not-decoded -->

## IV. CONFORMALIZED OFF-POLICY EVALUATION

Our objective is to get conformalized predictions for the value function of a policy π , based on training and calibration data gathered under a different behavior policy π b . We address this distribution shift by extending and improving the techniques developed in [28], [24]. We apply the CP formalism where the input X corresponds to the initial state, and the output Y to V π H ( X ) . Our method is illustrated in Figure 1. Next, we describe its components in detail. Specifically, (i) we explain how the aforementioned distribution shift can be addressed by weighing scores; (ii) we then discuss the important choice of the score function.

## A. Weighted conformal prediction

As suggested [28], [24], we can handle the distribution shift by weighing the scores using estimates of the likelihood ratio

<!-- formula-not-decoded -->

Fig. 1. Conformal prediction for off-policy evaluation. The dataset D is collected using a behavior policy π b , which is then split into the training D tr and calibration D cal datasets. When evaluating a different policy π , there is a shift in the data distribution, and we need to learn a likelihood ratios ˆ w to compensate for this shift. The training data is used to learn estimates of the weights ˆ w and a model ˆ f used in the computation of the scores. The estimated weights are used as plug-in estimates to re-weight the cumulative distribution function of the scores ˆ F x,y n , which is then used to compute the conformalized intervals ˆ C n ( x ) .

<!-- image -->

where for any policy π ′ ∈ { π, π b } , P π ′ X,Y ( x, y ) = P π ′ Y | X ( y | x ) p ( x ) denotes the distribution of the observation ( X,Y ) under π ′ ( P π ′ Y | X is this distribution given X ), and p ( x ) is the initial state distribution, which is the same in both cases. The value of a given trajectory τ = { x 1 , a 1 , r 1 , . . . , x H , a H , r H } is y = ∑ H t =1 r t . For any policy π ′ ∈ { π, π b } , the probability of observing τ under π ′ given the initial state x 1 = x is:

<!-- formula-not-decoded -->

Hence the weights can be written as:

<!-- formula-not-decoded -->

We make the following assumption to guarantee that the above weights are always well defined, and that the calibration data is i.i.d.

Assumption 1: We assume throughout the paper that P π ( ·| x ) is absolutely continuous w.r.t. P π b ( ·| x ) for all x ∈ X . We further assume that calibration data D cal provides n i.i.d. samples ( X i , Y i ) ∼ P π b X,Y .

<!-- formula-not-decoded -->

Then, we can compute the scores V i = s ( X i , Y i ) . For each possible pair ( x, y ) , using the normalized weights, we form the distribution ˆ F x,y n := ∑ n i =1 p w i ( x, y ) δ V i + p w n +1 ( x, y ) δ ∞ , with

and the conformalized set

<!-- formula-not-decoded -->

Proposition 1: Under Assumption 1, for any score function s and any α ∈ (0 , 1) ,

<!-- formula-not-decoded -->

where P π b ,π accounts for the randomness of ( X,Y ) ∼ P π X,Y and that of the data D cal = { X i , Y i } n i =1 (with for all i ∈ [ n ] , ( X i , Y i ) ∼ P π b X,Y ).

The proof of the proposition is similar to that of [24, Proposition 4.1], and is omitted due to space constraints. The complete proofs of all results can be found in the companion technical report 1 . Proposition 1 shows that, in absence of data from the target policy, we can still use a shifted CDF of the scores to assess the target policy. The result however relies on the assumption that the weights w ( x, y ) are known. In practice, we could use the training data to learn these weights, refer to Section V for details. The next proposition quantifies the impact of the error in this estimation procedure on the coverage. Its proof follows the same arguments as those in [24].

Proposition 2: Assume that the conformalized sets (3) are defined using estimated the weights ˆ w ( x, y ) satisfying E π b [ ˆ w ( X,Y ) r ] ≤ M r r &lt; ∞ for some r ≥ 2 . Define ∆ w = 1 2 E π b | ˆ w ( X,Y ) -w ( X,Y ) | . Then

<!-- formula-not-decoded -->

If, in addition, the non-conformity scores { V i } n i =1 have no ties almost surely, then we also have

<!-- formula-not-decoded -->

for some positive constant c depending on M r and r only.

## B. Selecting the score function

The choice of the score function critically impacts the size and center of the conformalized sets ˆ C n ( x ) . In previous work [21], [24], the pre-training procedure outputs some estimated quantiles q α lo ( x ) and q α hi ( x ) for the value of the behavior policy with initial state x , and the use of the symmetric score function

<!-- formula-not-decoded -->

is advocated. This choice yields a set ˆ C n ( x ) centered ¯ q π b ( x ) = ( q α lo ( x ) + q α hi ( x )) / 2 . Indeed, in view of (3) and (6), there is η ( x ) ∈ R such that ˆ C n ( x ) = [¯ q π b ( x ) -η ( x ) , ¯ q π b ( x ) + η ( x )] (note that when n grows large, η ( x ) becomes independent of x ). Having ˆ C n ( x ) centered on the estimated median value for π b is of course very problematic when the values of π b and π significantly differ. In this case, the length of ˆ C n ( x ) becomes unnecessarily large. Next we propose methods and score functions that efficiently re-center ˆ C n ( x ) around the value of π (instead of π b ), and that in turn yield much smaller conformalized sets.

1 Find the technical report and the code here https://github. com/danielefoffano/Conformal\_OPE\_MDP/blob/main/ Conformal\_OPE\_in\_MDP.pdf

Fig. 2. Symmetry problem. For the original confidence set with one single quantile, and score function s ( x, y ) = max( q α lo ( x ) -y, y -q α hi ( x )) , we obtain a set that is symmetric around its middle point ( q α lo ( x )+ q α hi ( x )) / 2 . We can break this symmetry by considering two different score quantiles, one for q α lo ( x ) -y and one for y -q α hi ( x ) , thus leading to a less conservative conformalized set.

<!-- image -->

1) Double-quantile score: a first idea is to break the symmetry of the score function used in [24] by considering the following confidence set

<!-- formula-not-decoded -->

where ˆ F x,y n, 0 := ∑ n i =1 p w i ( x, y ) δ V i, 0 + p w n +1 ( x, y ) δ ∞ and ˆ F x,y n, 1 := ∑ n i =1 p w i ( x, y ) δ V i, 1 + p w n +1 ( x, y ) δ ∞ , with V i, 0 = q α lo ( X i ) -Y i and V i, 1 = Y i -q α hi ( X i ) . In essence, we separately look at the lower and upper quantiles of the shifted distribution of the scores. A graphical illustration is provided in Fig. 2. The new construction of ˆ C n ( x ) does not affect coverage guarantees:

Proposition 3: Under Assumption 1, for α ∈ (0 , 1) the sets ˆ C n ( x ) in (7) satisfies

<!-- formula-not-decoded -->

We also obtain the following guarantees in case w ( x, y ) is replaced by ˆ w ( x, y ) .

Proposition 4: Let ˆ C n ( x ) be as in (7) with weights w ( x, y ) replaced by ˆ w ( x, y ) . Under the same assumptions as in Proposition 2, we have

<!-- formula-not-decoded -->

If, in addition, non-conformity scores { V i, 0 } n i =1 and { V i, 1 } n i =1 have no ties almost surely, then we also have

<!-- formula-not-decoded -->

for some positive constant c depending only on M r and r .

2) Shifted values: a second idea is to simply shift the values of the behavior policy π b using the likelihood ratios w ( x, y ) , as one would in important sampling methods. This can be done by simply using s ( x, y ) = y . This choice of score function makes sense intuitively: if we are interested in the value of the target policy π , then we may look at the shifted distribution of the values of the behavior policy.

We may also combine this choice with the double-quantile idea and construct ˆ C n ( x ) as

<!-- formula-not-decoded -->

where ˆ C n, 0 = { y ∈ R : y ≥ Quantile α/ 2 ( ˆ F x,y n )} and ˆ C n, 1 = { y ∈ R : y ≤ Quantile 1 -α/ 2 ( ˆ F x,y n )} . Propositions 3 and 4 also hold for this choice.

## V. OFFLINE ESTIMATION OF THE LIKELIHOOD RATIOS

In this section, we present various ways to estimate the likelihood ratios w ( x, y ) , and discuss their pros and cons.

## A. Monte-Carlo method

To estimate w ( x, y ) , we need to compute P π X,Y ( x, y ) and P π b X,Y ( x, y ) . Recall that the likelihood ratio is equal to

<!-- formula-not-decoded -->

where τ is a trajectory of length H . Since P π ( τ | x ) (sim. P π b ( τ | x ) ) depends on the transition kernel T and the reward distribution q , one needs to estimate these distributions from the data. We may proceed as follows:

- 1) We use the training data D tr to compute an estimate ( ˆ T, ˆ q ) of ( T, q ) (through maximum likelihood).
- 2) Compute an estimate of ˆ w ( x, y ) through Monte-Carlo sampling:

<!-- formula-not-decoded -->

where r ( k ) t and r ( k ) ′ t are sequences of rewards generated, respectively, by starting in x and following π and π b , and h is the number of Monte Carlo samples. These trajectories are generated using ˆ T and ˆ q , estimated in the previous step.

This approach has various shortcomings. First it requires us to estimate the model ( T, q ) . Then it forces us to generate a large number of trajectories, which is heavy computationally. Finally, the term 1 { y = ∑ H t =1 r t } is going to be 0 most of the times. A possible way to alleviate this issue consists in not including the last reward in the trajectory τ . This implies that we replace 1 { y = ∑ H t =1 r t } by ˆ q ( y -∑ H -1 n =1 r n | x H , a H ) . As it turns out, this naive Monte-Carlo method, used with success in simple scenarios (contextual bandits [24]), does not work in MDPs.

## B. Empirical and gradient-based methods

Next we present an alternative and more scalable way to estimate the weights w ( x, y ) from the training dataset D tr . We make use of the following simple rewriting of the likelihood ratio (also suggested in [24]):

<!-- formula-not-decoded -->

Next, observe that:

<!-- formula-not-decoded -->

Hence, learning w amounts to learning the following expectation:

<!-- formula-not-decoded -->

1) Empirical estimator: this method applies to the case x and y belong to some finite spaces X and Y only. In this case, we can directly estimate w ( x, y ) from the training data D tr by simply computing

<!-- formula-not-decoded -->

where the training data D tr consists of m trajectories generated under π b , the i -th trajectory in this dataset is τ i = ( x ( i ) t , a ( i ) t , r ( i ) t ) H t =1 , D tr ( x, y ) are trajectories with initial state and the accumulated reward x and y , respectively, and N ( x, y ) = |D tr ( x, y ) | . When the likelihood ratios are bounded, we can quantify the accuracy of the above estimates using standard concentration results:

Proposition 5: Let ( ε, δ ) ∈ (0 , 1) . Assume the ratio ∏ H t =1 π ( a t | x t ) / ∏ H t =1 π b ( a t | x t ) to be bounded in [ m,M ] for all possible trajectories of horizon H generated under π b . If min x,y N ( x, y ) ≥ ( M -m ) 2 2 ε 2 ln 2 |X||Y| δ , then

<!-- formula-not-decoded -->

Furthermore, we also have ∆ w ≤ ( M -m ) |X||Y| √ π 2 √ 2 min x,y N ( x,y ) .

The quantities M and m are usually function of the horizon H (in general one can choose m = 0 ). For example, in case A is finite, we obtain:

- In case π b and π are convex mixtures of a uniform distribution with another deterministic policy ˆ π , for example π ( a | x ) = ϵ |A| + (1 -ϵ ) 1 { a =ˆ π ( x ) } (sim. π b
- If π b is uniform over A , then an upper bound M is given by |A| H , and m = ( |A| min x,a π ( a | x )) H .

with ϵ b ), for some ϵ, ϵ b ≥ 0 , then one can choose M,m as

<!-- formula-not-decoded -->

In general, we see that the dependency on H is mild when π and π b that are somehow similar. As a future research direction, we could investigate possible ways to alleviate the impact of H (for example, by looking at the stationary rewards of the MDP, as in [15]).

See also Fig. 3 for an example of the scaling of M -m .

- 2) Gradient method: an alternative approach is to notice that w , as suggested in [24], can be seen as the solution of a MSE minimization problem. Indeed, w solves the following problem:

<!-- formula-not-decoded -->

Therefore, given some function approximator f θ parametrized by θ , we can minimize over θ the following empirical risk:

<!-- formula-not-decoded -->

As one would expect, this method still suffers from a large variance. For large horizons, it becomes quite difficult to learn the ratio of probabilities, especially when the two policies are extremely different. In fact for large H , in case the two policies are different, then it is likely that the ratio of action probabilities is 0 most of the time, with very few values different from 0 that tend to be extremely large. This makes the training procedure difficult, since most function approximators will just learn to output 0 .

## C. Algorithm

To conclude this section, we present a generic sketch of our proposed algorithm, see Algorithm 1 for a pseudocode. Following the split conformal prediction method, the algorithm first leverages the training data D tr to estimate the quantiles of the value of π b and the weights w . It then uses the calibration data D cal to compute the non-conformity scores. Using ˆ w as a plug-in estimate in the re-weighted

<!-- image -->

ϵ

Fig. 3. An example of the difference M -m for the case of a convex mixture, with |A| = 10 , H = 40 and ϵ b = 0 . 4 .

## Algorithm 1 Conformal Off-Policy Evaluation in MDPs

Require: Datasets D tr , D cal ; target coverage α ; policies ( π b , π ) ; score function s ; test input x test .

- 1: Use D tr to learn the quantiles q α lo ( x ) and q α hi ( x ) , as well as the weight ˆ w ( x, y ) using either the empirical estimator or the gradient-based method.
- 2: Compute ˆ F x,y n and the conformalized set ˆ C n ( x test ) using ˆ w ( x, y ) and the scores derived from the dataset D cal using either (3) or (7) or (9).

Return C n x

ˆ ( test )

scores distribution ˆ F x,y n , the algorithm can finally build the conformal prediction set ˆ C n ( x test ) .

## VI. NUMERICAL RESULTS

We evaluate our algorithms on the inventory problem [20], which can be modelled as an MDP with finite state and action spaces. We assume the behavior and target policies ( π, π b ) to be known, and to be ( ϵ, ϵ b ) -greedy with respect to the optimal policy π ⋆ . For example, for π , this means that for all ( x, a ) ,

<!-- formula-not-decoded -->

and similarly for π b with ϵ b . The optimal policy π ⋆ was computed by solving the infinite time-horizon discounted MDP, with discount factor γ = 0 . 99 . For each method, we evaluate the prediction interval for the cumulative return of the target policy π with different values of ϵ , while the behavior policy π b has ϵ b = 0 . 4 . By considering different values of ϵ for the target policy, we are able to observe how the coverage and interval length vary with respect to the distance between the target and the behavior policies.

## A. Environment

The inventory control problem is modelled as follows: an agent manages an inventory of size N while facing a stochastic demand for what is stored in it. At each round, the agent must choose how many items to buy to meet the upcoming order for the next day. The action set is the same for every state, i.e. A = [0 , N ] . We define the cost of buying a items as k 1 { a&gt; 0 } + c (min( N,x t + a ) -x t ) , where k &gt; 0 is the fixed cost for a single order and c &gt; 0 is the cost of a single unit bought. At each round, the agent earns a quantity pl , where p is the price of a single item and l is the number of items sold. Finally, the agent has to pay a cost zn for storing n &gt; 0 items, with z &gt; 0 and p &gt; z . The order o t is sampled from a Poisson distribution with rate λ . The next state is computed according to x t +1 = max(0 , min( N,x t + a t ) -o t +1 ) , while the reward is the sum of the costs and earnings listed above, i.e., r ( x t , a t , x t +1 ) = -k 1 { a t &gt; 0 } -zx t -c (min( N,x t + a t ) -x t ) + p max(0 , min( N,x t + a t ) -x t +1 ) . Note that here, the rewards are deterministic but depend on the next state - we can easily verify that all our results naturally extend to this setting. When testing our algorithm we chose the following parameters: N = 10 , k = 1 , c = 2 , z = 2 , p = 4 , λ = 10 .

## B. Algorithm details

We consider three different implementations of our algorithm: the first using the classical pinball score function [21], [24], the second using the double quantile method and finally the shifted values method with double quantile.

- 1) Pinball score function: this method adapts the algorithm presented in [24] to our setting (which is described in Section IV-B). We use the training dataset D tr to also learn two quantile networks ˆ q α lo and ˆ q α hi , with α lo = α/ 2 , α hi = 1 -α/ 2 (where α is the coverage parameter). The two functions are estimated using quantile regression and are modelled using two neural networks with two hidden layers of 64 nodes and ReLU activation functions. For this approach, the score function used is s ( x, y ) = max( y -ˆ q α hi , ˆ q α lo -y ) . Once we have computed the empirical CDF of the scores ˆ F x,y n , the confidence set is obtained using (3).
- 2) Double Quantile (DQ) method: Here we apply the method in IV-B.1. In this method, we introduce two score functions

<!-- formula-not-decoded -->

<!-- formula-not-decoded -->

where ˆ q α lo and ˆ q α hi are the same networks as in the previous method. Lastly, the confidence set is computed using (7).

- 3) Shifted Values (SV) with double quantile method: Here we consider a score function that allows us to shift the values of the behavior policy s ( x, y ) = y , as explained in IV-B.2, and compute the confidence set according to (9).

## C. Baseline: Quantile Estimation through Importance Sampling with Bootstrap (QIS-Bootstrap)

We compare the conformal prediction method developed in this work to quantile estimation through importance sampling [4] with bootstrap. Importance sampling (IS) has been widely used as a variance reduction technique in statistical methods, but in our case it can be used to perform off-policy evaluation as in [19], [26]. However, compared to [19], [26] that try to estimate the mean value of the target policy π , we use the IS technique to estimate the ( α lo , α hi ) -quantiles of the value of π . The key insight is that q π α ( x ) , the α -quantile of π in x , can be estimated using the calibration data D cal and the likelihood ratio w ( x, y ) through the following expression

<!-- formula-not-decoded -->

where I ( x ) = { y ∈ D cal : x 1 = x } , i.e. , we only consider the cumulative rewards of the trajectories in D cal that start in x .

The inner term can be seen as an empirical estimator of F π x ( y ) = E Y ∼ P π ( Y | X = x ) [ 1 { Y ≤ y } ] = E Y ∼ P π b ( Y | X = x ) [ w ( x, Y ) 1 { Y ≤ y } ] , the CDF of the values of π in x (note that the normalization factor does not affect the outcome, see also [4]). Since w ( x, y ) is unknown, we replace it by ˆ w ( x, y ) .

Next, rather than using the estimate q π α directly, to obtain a better estimate we use bootstrapping [27] to estimate a confidence interval around the α -quantile, obtaining a highconfidence interval ( q π α -, q π α + ) and then taking the median point ¯ q α ( x ) := ( q π α -+ q π α + ) / 2 . Finally, the confidence set for the value of π is simply given by

Fig. 4. Results for the inventory control problem for H = 20 , 40 , with target coverage of 90% . The policy π b is ϵ b -greedy w.r.t. π ⋆ (an optimal discounted policy with discount factor γ = 0 . 99 ), with ϵ b = 0 . 4 . We evaluated a target policy π that is ϵ -greedy w.r.t. π ⋆ , with varying ϵ . On the left: we show the boxplots of the average conformalized intervals for the various methods (whiskers indicate 95% confidence intervals for the minimum and the maximum). On the right we depict the coverage (bars indicate 95% confidence intervals).

<!-- image -->

<!-- formula-not-decoded -->

It is important to remember that there is no coverage guarantees for this set ˆ C n ( x ) .

## D. Results and discussion

In Figure 4, we show the results of our methods in the Inventory Problem for horizons 20 and 40, where results are averaged over 30 runs. Recall that the policy π b is ϵ b -greedy w.r.t. π ⋆ , with ϵ b = 0 . 4 , while π is ϵ -greedy w.r.t π ⋆ , with ϵ varying in [0 . 15 , 0 . 65] . The target level of coverage was chosen as 1 -α = 90% (depicted as the dashed black line in the plots of the second column). We evaluated our algorithms using the empirical estimate of ˆ w (see V-B.1) against the QIS-Bootstrap baseline method in Section VI-C.

1) Conformalized intervals: the plots in the left column illustrate the conformalized interval obtained for each method as a boxplot. For each run, method, and value of ϵ , we evaluated the confidence interval across 2000 tests-points x test sampled from p ( x ) , and averaged the corresponding minimum and maximum values of the confidence set ˆ C n ( x test ) . The whiskers indicate 95% confidence interval for the minimum and the maximum. As mentioned in Section IV-B, we observe that the pinball method yields an interval that enlarges/shrinks symmetrically around a fixed point. As a consequence, the interval becomes larger to maintain the desired coverage when the target policy π becomes really different than π b (i.e., ϵ is different than ϵ b = 0 . 4 ). Instead, with the proposed double quantile method, the interval is shifted depending on how far the target policy π is w.r.t. π b , leading to smaller intervals even when the policies are far from each other. The intervals estimated by the QIS-Bootstrap method match the ones of our new score functions when π is close to π b . However, when the policies are far from each other, the estimated interval is too conservative (i.e., too small and off-centred), which reflects in the coverage level of the algorithm, quickly degrading as π moves away from π b , for both horizons.

- 2) Coverage: the plots in the right column illustrate the achieved coverage, averaged over 30 runs (bars indicate 95% confidence interval). All the proposed conformalized methods achieved better levels of coverage than QIS-Bootstrap, as one would expect. For horizon H = 20 , the pinball method can maintain the desired level of coverage for all the epsilons at the expense of the interval length, while the new methods achieve a better level of coverage with a smaller interval size. For a larger horizon ( H = 40 ), we can see that the coverage of the QIS-Bootstrap method degrades very rapidly, maintaining the desired level only for π ≈ π b .

3) Discussion and future work: Some of the methods discussed to estimate the likelihood ratio w ( x, y ) were not used in our numerical experiments. This is mostly due to computational challenges: as we previously mentioned, the computational complexity of the Monte-Carlo method vastly exceeds the complexity of the other methods (empirical estimator and gradient method), while the gradient method has several difficulties in learning the likelihood ratios for values of ( ϵ, ϵ b ) that greatly differ. We plan to investigate how to efficiently learn the likelihood ratios using neural networks. Finally, we note that one may try conformalize the QIS-Bootstrap method in Section VI-C to have a more fair comparison.

## VII. CONCLUSION

In this work, we considered the offline off-policy evaluation problem in finite time-horizon Markov Decision Processes. Using Conformal Prediction (CP) techniques, we developed methods to construct conformalized intervals that include the true reward of the target policy with a prescribed level of certainty. Some of the challenges addressed in this paper include dealing with time-dependent data, as well as addressing the distribution shift between the behavior policy and the target policy. Furthermore, we proposed improved CP methods that allow to obtain intervals with significantly reduced length when compared to existing CP methods, while retaining the same certainty guarantees. We conclude with numerical results on the inventory control problem that demonstrated the efficiency of our methods. Several interesting research directions have been mentioned in the text, of which, the most significant, consists in improving the estimation of the likelihood ratio characterizing the distribution shift.

## REFERENCES

- [1] Léon Bottou, Jonas Peters, Joaquin Quiñonero-Candela, Denis X Charles, D Max Chickering, Elon Portugaly, Dipankar Ray, Patrice Simard, and Ed Snelson. Counterfactual reasoning and learning systems: The example of computational advertising. Journal of Machine Learning Research , 14(11), 2013.
- [2] Thomas G Dietterich and Jesse Hostetler. Conformal prediction intervals for markov decision process trajectories. arXiv preprint arXiv:2206.04860 , 2022.
- [3] Yaqi Duan, Zeyu Jia, and Mengdi Wang. Minimax-optimal offpolicy evaluation with linear function approximation. In International Conference on Machine Learning , pages 2701-2709. PMLR, 2020.
- [4] Peter W Glynn et al. Importance sampling for monte carlo estimation of quantiles. In Mathematical Methods in Stochastic Simulation and Experimental Design: Proceedings of the 2nd St. Petersburg Workshop on Simulation , pages 180-185. Citeseer, 1996.
- [5] Josiah Hanna, Peter Stone, and Scott Niekum. Bootstrapping with models: Confidence intervals for off-policy evaluation. In Proceedings of the AAAI Conference on Artificial Intelligence , volume 31, 2017.
- [6] Nan Jiang and Jiawei Huang. Minimax value interval for off-policy evaluation and policy optimization. Advances in Neural Information Processing Systems , 33:2747-2758, 2020.
- [7] Nathan Kallus and Masatoshi Uehara. Double reinforcement learning for efficient off-policy evaluation in markov decision processes. The Journal of Machine Learning Research , 21(1):6742-6804, 2020.
- [8] Nathan Kallus and Masatoshi Uehara. Efficiently breaking the curse of horizon in off-policy evaluation with double reinforcement learning. Operations Research , 2022.
- [9] Ilja Kuzborskij, Claire Vernade, Andras Gyorgy, and Csaba Szepesvári. Confident off-policy evaluation and selection through self-normalized importance weighting. In International Conference on Artificial Intelligence and Statistics , pages 640-648. PMLR, 2021.
- [10] Hoang Le, Cameron Voloshin, and Yisong Yue. Batch policy learning under constraints. In International Conference on Machine Learning , pages 3703-3712. PMLR, 2019.
- [11] Jing Lei and Larry Wasserman. Distribution-free prediction bands for non-parametric regression. Journal of the Royal Statistical Society: Series B (Statistical Methodology) , 76(1):71-96, 2014.
- [12] Lihua Lei and Emmanuel J Candès. Conformal inference of counterfactuals and individual treatment effects. Journal of the Royal Statistical Society Series B: Statistical Methodology , 83(5):911-938, 2021.
- [13] Lars Lindemann, Matthew Cleaveland, Gihyun Shim, and George J Pappas. Safe planning in dynamic environments using conformal prediction. arXiv preprint arXiv:2210.10254 , 2022.
- [14] Martin Lindh, Anders Karlén, and Ulf Norinder. Predicting the rate of skin penetration using an aggregated conformal prediction framework. Molecular Pharmaceutics , 14(5):1571-1576, 2017.
- [15] Qiang Liu, Lihong Li, Ziyang Tang, and Dengyong Zhou. Breaking the curse of horizon: Infinite-horizon off-policy estimation. Advances in Neural Information Processing Systems , 31, 2018.
- [16] Charles Lu, Ken Chang, Praveer Singh, and Jayashree Kalpathy-Cramer. Three applications of conformal prediction for rating breast density in mammography. arXiv preprint arXiv:2206.12008 , 2022.
- [17] Valery Manokhin. Awesome conformal prediction, April 2022. "If you use Awesome Conformal Prediction, please cite it as below.".
- [18] Harris Papadopoulos, Kostas Proedrou, Volodya Vovk, and Alex Gammerman. Inductive confidence machines for regression. In European Conference on Machine Learning , pages 345-356. Springer, 2002.
- [19] Doina Precup. Eligibility traces for off-policy policy evaluation. Computer Science Department Faculty Publication Series , page 80, 2000.
- [20] Martin L Puterman. Markov decision processes: discrete stochastic dynamic programming . John Wiley &amp; Sons, 2014.
- [21] Yaniv Romano, Evan Patterson, and Emmanuel Candes. Conformalized quantile regression. Advances in neural information processing systems , 32, 2019.
- [22] Chengchun Shi, Runzhe Wan, Victor Chernozhukov, and Rui Song. Deeply-debiased off-policy interval estimation. In International Conference on Machine Learning , pages 9580-9591. PMLR, 2021.
- [23] Chengchun Shi, Sheng Zhang, Wenbin Lu, and Rui Song. Statistical inference of the value function for reinforcement learning in infinitehorizon settings. Journal of the Royal Statistical Society Series B: Statistical Methodology , 84(3):765-793, 2022.
- [24] Muhammad Faaiz Taufiq, Jean-Francois Ton, Rob Cornish, Yee Whye Teh, and Arnaud Doucet. Conformal off-policy prediction in contextual bandits. arXiv preprint arXiv:2206.04405 , 2022.
- [25] Philip Thomas, Georgios Theocharous, and Mohammad Ghavamzadeh. High-confidence off-policy evaluation. In Proceedings of the AAAI Conference on Artificial Intelligence , volume 29, 2015.
- [26] Philip Thomas, Georgios Theocharous, and Mohammad Ghavamzadeh. High confidence policy improvement. In International Conference on Machine Learning , pages 2380-2388. PMLR, 2015.
- [27] Robert J Tibshirani and Bradley Efron. An introduction to the bootstrap. Monographs on statistics and applied probability , 57(1), 1993.
- [28] Ryan J Tibshirani, Rina Foygel Barber, Emmanuel Candes, and Aaditya Ramdas. Conformal prediction under covariate shift. Advances in neural information processing systems , 32, 2019.
- [29] Masatoshi Uehara, Chengchun Shi, and Nathan Kallus. A review of off-policy evaluation in reinforcement learning, 2022.
- [30] Vladimir Vovk, Alexander Gammerman, and Glenn Shafer. Algorithmic learning in a random world . Springer Science &amp; Business Media, 2005.
- [31] Wojciech Wisniewski, David Lindsay, and Sian Lindsay. Application of conformal prediction interval estimations to market makers' net positions. In Conformal and Probabilistic Prediction and Applications , pages 285-301. PMLR, 2020.
- [32] Zepu Xi, Xuebin Zhuang, and Hongbo Chen. Conformal prediction for hypersonic flight vehicle classification. In Conformal and Probabilistic Prediction with Applications , pages 118-206. PMLR, 2022.
- [33] Xianghao Zhan, Zhan Wang, Meng Yang, Zhiyuan Luo, You Wang, and Guang Li. An electronic nose-based assistive diagnostic prototype for lung cancer detection with conformal prediction. Measurement , 158:107588, 2020.