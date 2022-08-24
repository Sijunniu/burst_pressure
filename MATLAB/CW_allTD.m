%%% Investigation of burst pressure of fully simulated pipes %%%
%%% Flaw geometry is crack + wall loss corrosion %%%
%%% Initially written on 03/09/2022 %%%

clc
clear all
close all

% Load data and break down
load('CW_sTsD/CW_sTsD_data.mat')
load('CW_sTbD/CW_sTbD_data.mat')
load('CW_bTsD/CW_bTsD_data.mat')

% Switch to plot prediction for out-of-range variables
oor = 0;
load('CW_sTsD_oor.mat')
load('CW_sTbD_oor.mat')
load('CW_bTsD_oor.mat')
load('CW_diffW.mat')
burst_sTsD_oor = CW_sTsD_oor(:,4);
burst_sTbD_oor = CW_sTbD_oor(:,4);
burst_bTsD_oor = CW_bTsD_oor(:,4);
burst_diffW = CW_diffW(:,5);

% List out each individual parameters
depth = CW_sTsD_data(:,2);
length = CW_sTsD_data(:,3);
lig_2 = CW_sTsD_data(:,4);

% Burst pressure for case sTsD
burst_sTsD = CW_sTsD_data(:,6);
pb_ref_sTsD = 79.84;
p_sim = 78;
step1 = 0.75;
pb_sTsD = (p_sim * step1 + p_sim * (1-step1) * burst_sTsD) / pb_ref_sTsD;
pb_sTsD_oor = (p_sim * step1 + p_sim * (1-step1) * burst_sTsD_oor) / pb_ref_sTsD;
pb_sTsD_diffW = (p_sim * step1 + p_sim * (1-step1) * burst_diffW(1:2)) / pb_ref_sTsD;

% Burst pressure for case sTbD
burst_sTbD = CW_sTbD_data(:,6);
pb_ref_sTbD = 42.1;
p_sim = 42;
step1 = 0.75;
pb_sTbD = (p_sim * step1 + p_sim * (1-step1) * burst_sTbD) / pb_ref_sTbD;
pb_sTbD_oor = (p_sim * step1 + p_sim * (1-step1) * burst_sTbD_oor) / pb_ref_sTbD;
pb_sTbD_diffW = (p_sim * step1 + p_sim * (1-step1) * burst_diffW(3:4)) / pb_ref_sTbD;

% Burst pressure for case sTbD
burst_bTsD = CW_bTsD_data(:,6);
pb_ref_bTsD = 140.07;
p_sim = 140;
step1 = 0.8;
pb_bTsD = (p_sim * step1 + p_sim * (1-step1) * burst_bTsD) / pb_ref_bTsD;
pb_bTsD_oor = (p_sim * step1 + p_sim * (1-step1) * burst_bTsD_oor) / pb_ref_bTsD;
pb_bTsD_diffW = (p_sim * step1 + p_sim * (1-step1) * burst_diffW(5:6)) / pb_ref_bTsD;

pb = [pb_sTsD;...
      pb_sTbD;...
      pb_bTsD];
  
pb_oor = [pb_sTsD_oor;...
          pb_sTbD_oor;...
          pb_bTsD_oor];

pb_diffW = [pb_sTsD_diffW;...
            pb_sTbD_diffW;...
            pb_bTsD_diffW];
        
% Fit the data using Buckingham pi theorem
temp = [];
for i = 1:3
    if i == 1
        t = 15;
        D = 240;
        h_norm = [2:5] / t;
        l_norm = [2:5] / t;
        a_norm = [1:4] / t;
        ToverD = ones(64,1) * t / D;
    end
    if i == 2
        t = 15;
        D = 440;
        h_norm = [2:5] / t;
        l_norm = [2:5] / t;
        a_norm = [1:4] / t;
        ToverD = ones(64,1) * t / D;
    end
    if i == 3
        t = 25;
        D = 240;
        h_norm = [2:2:8] / t;
        l_norm = [2:2:8] / t;
        a_norm = [1:4] / t;
        ToverD = ones(64,1) * t / D;
    end
    [L, A, H] = meshgrid(l_norm, a_norm, h_norm);  % as in order x, y, z
    H = reshape(H, [64, 1]);
    L = reshape(L, [64, 1]);
    A = reshape(A, [64, 1]);
    temp = [temp; H A L ToverD];
end
tbl = table(temp(:,1), temp(:,2), temp(:,3), temp(:,4), pb);
modelfun = @(c,x)1 + c(1)*(x(:,1).^c(2)).*(x(:,2).^c(3)).*(x(:,3).^c(4)).*(x(:,4).^c(5));
beta0 = [-1 1 0.1 -0.2 -0.1];  % initial guess for the coeff
mdl = fitnlm(tbl,modelfun,beta0)  % do the fitting
fc = mdl.Coefficients{:,1};  % fitted coeff

% Do a linear plot after the dimensional analysis
x = linspace(0, 1.5, 50);
y = 1 + fc(1)*x;
pb_x = temp(:,1).^fc(2).*temp(:,2).^fc(3).*temp(:,3).^fc(4).*temp(:,4).^fc(5);
figure
hold on
grid on
box on
plot(pb_x(129:192), pb(129:192), 'o', 'linewidth', 2, 'markersize', 10)
plot(pb_x(1:64), pb(1:64), 'o', 'linewidth', 2, 'markersize', 10)
plot(pb_x(65:128), pb(65:128), 'o', 'linewidth', 2, 'markersize', 10)
plot(x,y,'k', 'linewidth', 3)
legend('D/t=9.6 FEA', 'D/t=16 FEA', 'D/t=29.3 FEA','Linear regression')
xlabel('${(d/t)^{0.524}(a/t)^{0.198}(l/t)^{-0.342}(D/t)^{0.115}}$','interpreter','latex')
ylabel('Normalized burst pressure')
set(gca,'FontSize',40)
set(gca,'YColor','k')
set(gca,'LineWidth',2);
set(gcf,'Units','Inches');
set(gcf,'Position',[2 0.2 1.5*10. 1.37*7.5])

if oor
    depth_oor = [];
    length_oor = [];
    lig_2_oor = [];
    depth_diffW = [];
    length_diffW = [];
    lig_2_diffW = [];
    ToverD_oor = [];
    ToverD_diffW = [];
    for i = 1:3
        if i == 1
            t = 15;
            D = 240;
        elseif i == 2
            t = 15;
            D = 440;
        elseif i == 3
            t = 25;
            D = 240;
        end
        depth_oor = [depth_oor; CW_sTsD_oor(:,1) / t];
        length_oor = [length_oor; CW_sTsD_oor(:,2) / t];
        lig_2_oor = [lig_2_oor; CW_sTsD_oor(:,3) / t];
        ToverD_oor = [ToverD_oor; ones(size(CW_sTsD_oor(:,1))) * t / D];
        depth_diffW = [depth_diffW; CW_diffW(1:2,1) / t];
        length_diffW = [length_diffW; CW_diffW(1:2,2) / t];
        lig_2_diffW = [lig_2_diffW; CW_diffW(1:2,3) / t];
        ToverD_diffW = [ToverD_diffW; ones(size(CW_diffW(1:2,1))) * t / D];
    end
    pb_oor_x = depth_oor.^fc(2).*length_oor.^fc(3).*lig_2_oor.^fc(4).*ToverD_oor.^fc(5);
    pb_diffW_x = depth_diffW.^fc(2).*length_diffW.^fc(3).*lig_2_diffW.^fc(4).*ToverD_diffW.^fc(5);
    figure
    hold on
    grid on
    box on
    plot(pb_x, pb, 'o', 'linewidth', 2, 'markersize', 10)
    plot(pb_oor_x, pb_oor, '^', 'linewidth', 2, 'markersize', 15)
    plot(pb_diffW_x, pb_diffW, 's', 'linewidth', 2, 'markersize', 15)
    plot(x,y,'k', 'linewidth', 3)
    xlabel('${(d/t)^{0.524}(a/t)^{0.198}(l/t)^{-0.342}(D/t)^{0.115}}$','interpreter','latex')
    ylabel('Normalized burst pressure')
    legend('Original data', 'Out of range data','Different loss width')
    set(gca,'FontSize',40)
    set(gca,'YColor','k')
    set(gca,'LineWidth',2);
    set(gcf,'Units','Inches');
    set(gcf,'Position',[2 0.2 1.5*10. 1.37*7.5])
end