%%% Investigation of burst pressure of fully simulated pipes %%%
%%% Flaw geometry is two cracks %%%
%%% Initially written on 06/01/2022 %%%

clc
clear all
close all

% Load data and break down
load('CC_bTsD_data.mat')

% List out each individual parameters
length_1 = CC_bTsD_data(:,2);
length_2 = CC_bTsD_data(:,3);
lig_1 = CC_bTsD_data(:,4);
lig_2 = CC_bTsD_data(:,5);
lig_3 = CC_bTsD_data(:,6);
burst_time = CC_bTsD_data(:,7);

% Other parameters
t = 25; % pipe thickness (mm)
D = 240; % pipe outer diameter (mm)

% Burst criteria (MPa)
max_mises_1 = 533.5; % 69 + yield stress

% Reference burst pressure for pipe without flaw
pb_ref_1 = 140.07;

% Applied pressure in the simulations
p_sim_1 = 112;
p_sim_2 = 140;

% Convert time to pressure then normalize
pb_1 = (p_sim_1 + (p_sim_2 - p_sim_1) * burst_time) / pb_ref_1;

% Fit the data using Buckingham pi theorem
a1_norm = [1:2:5] / t;
a2_norm = [1:2:5] / t;
l1_norm = [2:2:6] / t;
l2_norm = [2:2:6] / t;
[A1, A2, L1, L2] = ndgrid(a1_norm, a2_norm, l1_norm, l2_norm);  % as in order x, y, z, w
A1 = reshape(A1, [81, 1]);
A2 = reshape(A2, [81, 1]);
L1 = reshape(L1, [81, 1]);
L2 = reshape(L2, [81, 1]);
tbl = table(A1, A2, L1, L2, pb_1);  % data from simulation is in reverse order
modelfun = @(c,x)1 + c(1)*(x(:,1).^c(2)).*(x(:,2).^c(3)).*(x(:,3).^c(4)).*(x(:,4).^c(5));
beta0 = [-1 0.1 0.1 -0.2 -0.2];  % initial guess for the coeff
mdl = fitnlm(tbl,modelfun,beta0)  % do the fitting
fc = mdl.Coefficients{:,1};  % fitted coeff

% Do a linear plot after the dimensional analysis
x = linspace(0, 2.5, 50);
y = 1 + fc(1)*x;
pb_x = A1.^fc(2).*A2.^fc(3).*L1.^fc(4).*L2.^fc(5);
figure
hold on
grid on
box on
plot(x,y,'k', 'linewidth', 3)
plot(pb_x, pb_1, 'o', 'linewidth', 2, 'markersize', 12)
legend('Linear fit', 'FEA data')
xlabel('${(a_1/t)^{0.465}(a_2/t)^{0.077}(l_1/t)^{-0.448}(l_2/t)^{-0.173}}$','interpreter','latex')
ylabel('Normalized burst pressure')
set(gca,'FontSize',40)
set(gca,'YColor','k')
set(gca,'LineWidth',2);
set(gcf,'Units','Inches');
set(gcf,'Position',[2 0.2 1.5*10. 1.37*7.5])