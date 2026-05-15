# Technical summary — (title not detected)

Authors: unknown
Source: assets/Foffano et al. - 2023 - Conformal Off-Policy Evaluation in Markov Decision Processes.pdf (SHA b85a8bca8909)
Generated: 2026-05-15T13:19:29.824623+00:00
Formula enrichment: false

## Equations

### From "B. Standard Conformal Prediction" (p. 2)

```
1 -α ≤ P ( Y ∈ ˆ C n ( X )) ≤ 1 -α + 1 n +1 . (1)
```
*Equation (1)* — , ( X n +1 , Y n +1 ) are exchangeable, this construction ensures coverage with certainty level 1 -α :

### From "A. Weighted conformal prediction" (p. 2)

```
w ( x, y ) := d P π X,Y d P π b X,Y ( x, y ) = d P π Y | X d P π b Y | X ( y | x ) ,
```
*Equation (2)* — As suggested [28], [24], we can handle the distribution shift by weighing the scores using estimates of the likelihood ratio

```
P π ′ ( τ | x ) = π ′ ( a 1 | x ) q ( r 1 | x, a 1 ) H ∏ t =2 π ′ ( a t | x t ) × T ( x t | x t -1 , a t -1 ) q ( r t | x t , a t ) .
```
*Equation (3)* — For any policy π ′ ∈ { π, π b } , the probability of observing τ under π ′ given the initial state x…

```
w ( x, y ) = ∫ 1 { y = ∑ H t =1 r t } P π ( τ | x )d τ ∫ 1 { y = ∑ H t =1 r t } P π b ( τ | x )d τ .
```
*Equation (4)* — Hence the weights can be written as:

```
p w i ( x, y ) =        w ( X i , Y i ) ∑ n j =1 w ( X j , Y j ) + w ( x, y ) if i ≤ n, w ( x, y ) ∑ n j =1 w ( X j , Y j ) + w ( x, y ) if i = n +1 , (2)
```
*Equation (5)* — samples ( X i , Y i ) ∼ P π b X,Y

```
ˆ C n ( x ) := { y ∈ R : s ( x, y ) ≤ Quantile 1 -α ( ˆ F x,y n )} . (3)
```
*Equation (6)* — and the conformalized set

```
P π b ,π [ Y ∈ ˆ C n ( X ) ] ≥ 1 -α, (4)
```
*Equation (7)* — Proposition 1: Under Assumption 1, for any score function s and any α ∈ (0 , 1) ,

```
P π b ,π [ Y ∈ ˆ C n ( X ) ] ≥ 1 -α -∆ w , (5)
```
*Equation (8)* — Then

```
P π b ,π [ Y ∈ ˆ C n ( X ) ] ≤ 1 -α +∆ w + cn 1 /r -1 ,
```
*Equation (9)* — If, in addition, the non-conformity scores { V i } n i =1 have no ties almost surely, then we also have

### From "B. Selecting the score function" (p. 3)

```
s ( x, y ) = max( q α lo ( x ) -y, y -q α hi ( x )) , (6)
```
*Equation (10)* — In previous work [21], [24], the pre-training procedure outputs some estimated quantiles q α lo ( x ) and q α hi ( x )…

```
ˆ C n ( x ) := { y ∈ R : q α lo ( x ) -y ≤ Quantile 1 -α/ 2 ( ˆ F x,y n, 0 )} ∩ { y ∈ R : y -q α hi ( x ) ≤ Quantile 1 -α/ 2 ( ˆ F x,y n, 1 )} , (7)
```
*Equation (11)* — 1) Double-quantile score: a first idea is to break the symmetry of the score function used in [24] by considering the following confidence set

```
P π b ,π [ Y ∈ ˆ C n ( X ) ] ≥ 1 -α. (8)
```
*Equation (12)* — Proposition 3: Under Assumption 1, for α ∈ (0 , 1) the sets ˆ C n ( x ) in (7) satisfies

```
P π b ,π [ Y ∈ ˆ C n ( X ) ] ≥ 1 -α -∆ w .
```
*Equation (13)* — Under the same assumptions as in Proposition 2, we have

```
P π b ,π [ Y ∈ ˆ C n ( X ) ] ≤ 1 -α +∆ w + cn 1 /r -1 ,
```
*Equation (14)* — If, in addition, non-conformity scores { V i, 0 } n i =1 and { V i, 1 } n i =1 have no ties…

```
ˆ C n ( x ) = ˆ C n, 0 ( x ) ∩ ˆ C n, 1 ( x ) , (9)
```
*Equation (15)* — We may also combine this choice with the double-quantile idea and construct ˆ C n ( x ) as

### From "A. Monte-Carlo method" (p. 4)

```
w ( x, y ) = ∫ 1 { y = ∑ H t =1 r t } P π ( τ | x )d τ ∫ 1 { y = ∑ H t =1 r t } P π b ( τ | x )d τ ,
```
*Equation (16)* — Recall that the likelihood ratio is equal to

```
ˆ w ( x, y ) = (1 /h ) ∑ h k =1 1 { y = ∑ H t =1 r ( k ) t } (1 /h ) ∑ h k =1 1 { y = ∑ H t =1 r ( k ) ′ t } , (10)
```
*Equation (17)* — We may proceed as follows:

### From "B. Empirical and gradient-based methods" (p. 5)

```
w ( x, y ) = P π X,Y ( x, y ) P π b X,Y ( x, y ) , = ∫ P π X,Y ( x, y ) P π b X,Y ( x, y ) P π b τ | X,Y ( τ | x, y ) P π b τ | X,Y ( τ | x, y ) P π τ | X,Y ( τ | x, y )d τ, = ∫ P π X,Y,τ ( x, y, τ ) P π b X,Y,τ ( x, y, τ ) P π b τ | X,Y ( τ | x, y )d τ, = E τ ∼ P π b τ | X = x,Y = y [ P π X,Y,τ ( x, y, τ ) P π b X,Y,τ ( x, y, τ ) ] .
```
*Equation (18)* — We make use of the following simple rewriting of the likelihood ratio (also suggested in [24]):

```
P π X,Y,τ ( x, y, τ ) P π b X,Y,τ ( x, y, τ ) = P ( y | x, τ ) P π ( τ | x ) P ( y | x, τ ) P π b ( τ | x ) = ∏ H t =1 π ( a t | x t ) ∏ H t =1 π b ( a t | x t ) .
```
*Equation (19)* — Next, observe that:

```
w ( x, y ) = E τ ∼ P π b τ | X = x,Y = y [ ∏ H t =1 π ( a t | x t ) ∏ H t =1 π b ( a t | x t ) ] . (11) To this aim, we propose the following two approaches.
```
*Equation (20)* — Hence, learning w amounts to learning the following expectation:

```
ˆ w ( x, y ) = 1 N ( x, y ) ∑ τ i ∈D tr ( x,y ) ∏ H t =1 π ( a ( i ) t | x ( i ) t ) ∏ H t =1 π b ( a ( i ) t | x ( i ) t ) , (12)
```
*Equation (21)* — In this case, we can directly estimate w ( x, y ) from the training data D tr by simply computing

```
P π b [ | ˆ w ( X,Y ) -w ( X,Y ) | > ε ] < δ.
```
*Equation (22)* — If min x,y N ( x, y ) ≥ ( M -m ) 2 2 ε 2 ln 2 |X||Y| δ , then

```
M 1 /H = max ( ϵ ϵ b , (1 -ϵ ) + ϵ/ |A| (1 -ϵ b ) + ϵ b / |A| ) , m 1 /H = min ( ϵ ϵ b , (1 -ϵ ) + ϵ/ |A| (1 -ϵ b ) + ϵ b / |A| ) .
```
*Equation (23)* — with ϵ b ), for some ϵ, ϵ b ≥ 0 , then one can choose M,m as

```
min f E ( X,Y,τ ) ∼ P π b X,Y,τ   ( ∏ H t =1 π ( a t | x t ) ∏ H t =1 π b ( a t | x t ) -f ( X,Y ) ) 2   . (13)
```
*Equation (24)* — 3 for an example of the scaling of M -m

```
1 m ∑ τ i ∈D tr ( ∏ H t =1 π ( a ( i ) t | x ( i ) t ) ∏ H t =1 π b ( a ( i ) t | x ( i ) t ) -f θ ( x ( i ) 1 , H ∑ t =1 r ( i ) t )) 2 .
```
*Equation (25)* — Therefore, given some function approximator f θ parametrized by θ , we can minimize over θ the following empirical risk:

### From "VI. NUMERICAL RESULTS" (p. 6)

```
π ( a | x ) = ϵ |A| +(1 -ϵ ) 1 { a = π ⋆ ( x ) } ,
```
*Equation (26)* — For example, for π , this means that for all ( x, a ) ,

### From "B. Algorithm details" (p. 6)

```
s 0 ( x, y ) = ˆ q α lo ( x ) -y s ( x, y ) = y ˆ q ( x )
```
*Equation (27)* — We consider three different implementations of our algorithm: the first using the classical pinball score function [21], [24], the second using the double quantile method…

```
1 -α hi ,
```
*Equation (28)* — We consider three different implementations of our algorithm: the first using the classical pinball score function [21], [24], the second using the double quantile method…

### From "C. Baseline: Quantile Estimation through Importance Sampling with Bootstrap (QIS-Bootstrap)" (p. 6)

```
q π α ( x ) = Quantile α   ∑ y ∈I ( x ) w ( x, y ) ∑ y ′ ∈I ( x ) w ( x, y ′ ) δ y   ,
```
*Equation (29)* — The key insight is that q π α ( x ) , the α -quantile of π in x , can be estimated using the…

```
ˆ C n ( x ) = [¯ q α lo ( x ) , ¯ q α hi ( x )] . (14)
```
*Equation (30)* — Horizon 40
