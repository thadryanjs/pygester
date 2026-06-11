# Technical summary — Control-Oriented Model-Based Reinforcement Learning with Implicit Differentiation

Authors: Evgenii Nikishin, 1 Romina Abachi, 2 Rishabh Agarwal, 1 3 Pierre-Luc Bacon 1 4, 1 Mila, Universit´ e de Montr´ eal, 2 Vector Institute, University of Toronto 3 Google Research, Brain Team, 4 Facebook CIFAR AI Chair evgenii.nikishin@mila.quebec
Source: assets/Nikishin et al. - 2022 - Control-Oriented Model-Based Reinforcement Learning with Implicit Differentiation.pdf (SHA cc68c21c6ba0)
Generated: 2026-06-11T15:59:54.903623+00:00
Formula enrichment: false

## Abstract

The shortcomings of maximum likelihood estimation in the context of model-based reinforcement learning have been highlighted by an increasing number of papers. When the model class is misspecified or has a limited representational capacity, model parameters with high likelihood might not necessarily result in high performance of the agent on a downstream control task. To alleviate this problem, we propose an end-to-end approach for model learning which directly optimizes the expected returns using implicit differentiation. We treat a value function that satisfies the Bellman optimality operator induced by the model as an implicit function of model parameters and show how to differentiate the function. We provide theoretical and empirical evidence highlighting the benefits of our approach in the model misspecification regime compared to likelihood-based methods.

## Equations

### From "3 Preliminaries" (p. 2)

```
min θ E s,a,s ′ [ ‖ f θ ( s, a ) -s ′ ‖ 2 ] , min θ E s,a,r [ ( r θ ( s, a ) -r ) 2 ] . (1)
```
*Equation (1)* — For example, if the true model is assumed to be Gaussian with a parameterized mean ( f θ , r θ ) and a fixed…

### From "4 Optimal Model Design for Tabular MDPs" (p. 2)

```
max Q,θ J ( π Q ) s.t. Q ( s, a ) = B θ Q ( s, a ) ∀ s ∈ S , a ∈ A , where π Q ( a | s ) = exp Q ( s, a ) ∑ a ′ exp Q ( s, a ′ ) . (2)
```
*Equation (2)* — The optimization problem becomes

```
B θ Q ( s, a ) ≜ r θ ( s, a ) + γ E p θ ( s ′ | s,a ) log ∑ a ′ exp Q ( s ′ , a ′ ) . (3)
```
*Equation (3)* — B θ here is the soft Bellman optimality operator with respect to the model parameters θ

```
θ ϕ - → Q ∗ exp - - → π Q ∗ act - → J. (4)
```
*Equation (4)* — The sequence of transformations from the model parameters to the agent's performance can be described then using the following graph

```
∂J ( θ ) ∂θ = ∂J ( π ) ∂π ︸ ︷︷ ︸ PG · ∂π ( Q ∗ ) ∂Q ∗ ︸ ︷︷ ︸ softmax · ∂ϕ ( θ ) ∂θ ︸ ︷︷ ︸ IFT . (5)
```
*Equation (5)* — 1999), we can apply automatic differentiation to calculate the gradient with respect to θ

```
min Q,θ L true ( Q ) ≜ ∑ s,a ( Q ( s, a ) -BQ ( s, a )) 2 , s.t. Q ( s, a ) = B θ Q ( s, a ) ∀ s ∈ S , a ∈ A , (6)
```
*Equation (6)* — However, we can make it a value-based approach (Watkins and Dayan 1992) by replacing the objective J ( π Q ) with the Bellman error

### From "4.1 Implicit Differentiation" (p. 3)

```
∂ϕ ( θ ) ∂θ = -( ∂f ( θ, w ∗ ) ∂w ) -1 · ∂f ( θ, w ∗ ) ∂θ ∣ ∣ ∣ w ∗ = ϕ ( θ ) . (7)
```
*Equation (7)* — Moreover

### From "4.2 Benefits under Model Misspecification" (p. 3)

```
θ = { κ ‖ θ ‖ θ if ‖ θ ‖ > κ, θ if ‖ θ ‖ ≤ κ . (8)
```
*Equation (8)* — We then apply the projected gradient ascent where after each step we make a projection on a space of bounded parameters via

```
DKL ( p || p θ ) = 1 |S| · |A| ∑ s,a,s ′ p ( s ′ | s, a ) log p ( s ′ | s, a ) p θ ( s ′ | s, a )
```
*Equation (9)* — Finding an MLE solution corresponds to minimizing the average KL divergence

### From "5.1 Optimal Solutions for OMD" (p. 4)

```
B θ Q ∗ ( s, a ) = B θ ′ Q ∗ ( s, a ) ∀ s ∈ S , a ∈ A . (9)
```
*Equation (10)* — Models with parameters θ and θ ′ are Q ∗ -equivalent if

```
lim α → 0 α log ∑ a ′ exp 1 α Q ( s ′ , a ′ ) = max a ′ Q ( s ′ , a ′ ) . (10)
```
*Equation (11)* — As the log-sum-exp temperature in (3) approaches 0, we recover the 'hard' target in the Bellman optimality operator

### From "5.2 Approximation Bound" (p. 4)

```
max s,a ∣ ∣ ∣ Q ∗ ( s, a ) -ˆ Q MLE ( s, a ) ∣ ∣ ∣ ≤ ϵ r 1 -γ + γϵ p r max 2(1 -γ ) 2 ;
```
*Equation (12)* — Let ˆ Q OMD and ˆ Q MLE be the fixed points of the Bellman optimality operators for approximate OMD and MLE models respectively

```
max s,a ∣ ∣ ∣ Q ∗ ( s, a ) -ˆ Q OMD ( s, a ) ∣ ∣ ∣ ≤ ϵ 1 -γ .
```
*Equation (13)* — Let ˆ Q OMD and ˆ Q MLE be the fixed points of the Bellman optimality operators for approximate OMD and MLE models respectively

### From "6 OMDwith Function Approximation" (p. 5)

```
min w L ( θ, w ) ≜ min w E s,a [ Q w ( s, a ) -B θ Q ¯ w ( s, a )] 2 , (11)
```
*Equation (14)* — The network is trained to minimize the Bellman error induced by the model θ

```
∂L ( θ, w ) ∂w = 0 . (12)
```
*Equation (15)* — We introduce an alternative but similar constraint, the first-order optimality condition for minimizing the Bellman error (11)

### From "Algorithm 1: Model Based RL with OMD" (p. 5)

```
L true ( w ) ≜ E s,a [ Q w ( s, a ) -BQ ¯ w ( s, a )] 2 , (13)
```
*Equation (16)* — We consider the problem (6) and use the Bellman error as the outer loop objective

```
BQ ¯ w ( s, a ) ≜ r ( s, a ) + γ E p ( s ′ | s,a ) log ∑ a ′ exp Q ¯ w ( s ′ , a ′ ) .
```
*Equation (17)* — where B , again, is a soft Bellman operator induced by the true reward r and dynamics p

```
∂L true ( θ ) ∂θ ≈ -∂L true ( w ∗ ) ∂w ︸ ︷︷ ︸ grad Bellman · ∂ 2 L ( θ, w ∗ ) ∂θ∂w ︸ ︷︷ ︸ approx IFT ∣ ∣ ∣ w ∗ = ϕ ( θ ) (14)
```
*Equation (18)* — The Q function and IFT approximations result in the following gradient with respect to θ

### From "7 Experiments with Function Approximation" (p. 6)

```
ℓ VEP ( θ ) = ∑ π ∈ Π ∑ V ∈V ∑ s ∈S ( B π V ( s ) -B θ π V ( s ) ) 2 , (15)
```
*Equation (19)* — The VEP model minimizes the difference between the Bellman operators
