%%% Investigation of burst pressure of fully simulated pipes %%%
%%% Material is X42, X65 and X100 steel %%%
%%% Flaw geometry is crack + wall loss corrosion %%%
%%% Initially written on 03/17/2022 %%%

clc
clear all
close all

% Load data and break down
load('X42/CW_X42_data.mat')
load('CW_sTsD/CW_sTsD_data.mat')
load('X100/CW_X100_data.mat')

% Pipe thickness
t = 15;
D = 240;

% Three burst pressures
burst_X42 = CW_X42_data(:,6);
pb_ref_X42 = 60;
p_sim_1 = 40;
p_sim_2 = 60;
pb_X42 = (p_sim_1 + (p_sim_2 - p_sim_1) * burst_X42) / pb_ref_X42;

burst_X65 = CW_sTsD_data(:,6);
pb_ref_X65 = 79.84;
p_sim_1 = 58.5;
p_sim_2 = 78;
pb_X65 = (p_sim_1 + (p_sim_2 - p_sim_1) * burst_X65) / pb_ref_X65;

burst_X100 = CW_X100_data(:,6);
pb_ref_X100 = 110.8;
p_sim_1 = 90;
p_sim_2 = 110;
pb_X100 = (p_sim_1 + (p_sim_2 - p_sim_1) * burst_X100) / pb_ref_X100;

% Fit the data using Buckingham pi theorem
h_norm = [2, 3.5, 5] / t;
l_norm = [2, 3.5, 5] / t;
a_norm = [1, 2.5, 4] / t;
[L, A, H] = meshgrid(l_norm, a_norm, h_norm);  % as in order x, y, z
H = reshape(H, [27, 1]);
L = reshape(L, [27, 1]);
A = reshape(A, [27, 1]);

% For X42
tbl_X42 = table(H, A, L, pb_X42);  % data from simulation is in reverse order
modelfun = @(c,x)1 + c(1)*(x(:,1).^c(2)).*(x(:,2).^c(3)).*(x(:,3).^c(4));
beta0 = [-1 1 0.1 -0.2];  % initial guess for the coeff
mdl = fitnlm(tbl_X42,modelfun,beta0)  % do the fitting
fc_X42 = mdl.Coefficients{:,1};  % fitted coeff
pb_x_X42 = H.^fc_X42(2).*A.^fc_X42(3).*L.^fc_X42(4);

% For X100
tbl_X100 = table(H, A, L, pb_X100);  % data from simulation is in reverse order
modelfun = @(c,x)1 + c(1)*(x(:,1).^c(2)).*(x(:,2).^c(3)).*(x(:,3).^c(4));
beta0 = [-1 1 0.1 -0.2];  % initial guess for the coeff
mdl = fitnlm(tbl_X100,modelfun,beta0)  % do the fitting
fc_X100 = mdl.Coefficients{:,1};  % fitted coeff
pb_x_X100 = H.^fc_X100(2).*A.^fc_X100(3).*L.^fc_X100(4);

h_norm = [2, 3, 4, 5] / t;
l_norm = [2, 3, 4, 5] / t;
a_norm = [1, 2, 3, 4] / t;
[L, A, H] = meshgrid(l_norm, a_norm, h_norm);  % as in order x, y, z
H = reshape(H, [64, 1]);
L = reshape(L, [64, 1]);
A = reshape(A, [64, 1]);

% For X65
tbl_X65 = table(H, A, L, pb_X65);  % data from simulation is in reverse order
modelfun = @(c,x)1 + c(1)*(x(:,1).^c(2)).*(x(:,2).^c(3)).*(x(:,3).^c(4));
beta0 = [-1 1 0.1 -0.2];  % initial guess for the coeff
mdl = fitnlm(tbl_X65,modelfun,beta0)  % do the fitting
fc_X65 = mdl.Coefficients{:,1};  % fitted coeff
pb_x_X65 = H.^fc_X65(2).*A.^fc_X65(3).*L.^fc_X65(4);

% Do a linear plot after the dimensional analysis
x = linspace(0, 1, 50);
y_X42 = 1 + fc_X42(1)*x;
y_X65 = 1 + fc_X65(1)*x;
y_X100 = 1 + fc_X100(1)*x;

figure
hold on
grid on
box on
plot(pb_x_X42, pb_X42, 'o', 'linewidth', 2, 'markersize', 10)
plot(pb_x_X65, pb_X65, 'o', 'linewidth', 2, 'markersize', 10)
plot(pb_x_X100, pb_X100, 'o', 'linewidth', 2, 'markersize', 10)
plot(x,y_X42,'k', 'linewidth', 3)
plot(x,y_X65,'k', 'linewidth', 3)
plot(x,y_X100,'k', 'linewidth', 3)
legend('X42 FEA','X65 FEA','X100 FEA')
ylabel('Normalized burst pressure')
set(gca,'FontSize',40)
set(gca,'YColor','k')
set(gca,'LineWidth',2);
set(gcf,'Units','Inches');
set(gcf,'Position',[2 0.2 1.5*10. 1.37*7.5])

% Plot the coefficients as a function of the X grade
c2 = [fc_X42(2),fc_X65(2),fc_X100(2)] / fc_X42(2);
c3 = [fc_X42(3),fc_X65(3),fc_X100(3)] / fc_X42(3);
c4 = [fc_X42(4),fc_X65(4),fc_X100(4)] / fc_X42(4);

figure
hold on
box on
plot(c2, '-o', 'linewidth', 2, 'markersize', 10)
plot(c3, '-o', 'linewidth', 2, 'markersize', 10)
plot(c4, '-o', 'linewidth', 2, 'markersize', 10)
legend('c2','c3','c4')
set(gca,'xtick',[1:3],'xticklabel',{'X42','X65','X100'})
set(gca,'FontSize',40)
set(gca,'YColor','k')
set(gca,'LineWidth',2);
set(gcf,'Units','Inches');
set(gcf,'Position',[2 0.2 1.5*10. 1.37*7.5])