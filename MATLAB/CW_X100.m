%%% Investigation of burst pressure of fully simulated pipes %%%
%%% Material is X100 steel %%%
%%% Flaw geometry is crack + wall loss corrosion %%%
%%% Initially written on 03/17/2022 %%%

clc
clear all
close all

% Load data and break down
load('CW_X100_data.mat')

% If doing a fitting
switch_1dplt = 0;
switch_2dplt = 0;
switch_linplt = 1;

param = 'lig'; % Choose primary variables

% List out each individual parameters
depth = CW_X100_data(:,2);
length = CW_X100_data(:,3);
lig_2 = CW_X100_data(:,4);
lig_1 = CW_X100_data(:,5);
burst_time = CW_X100_data(:,6);

% Other parameters
t = 15; % pipe thickness (mm)
D = 240; % pipe outer diameter (mm)

% Burst criteria (MPa)
max_mises_1 = 740; % determined from simulation

% Reference burst pressure for pipe without any flaw
pb_ref_1 = 110.8;

% Applied pressure in the simulations
p_sim_1 = 90;
p_sim_2 = 110;

% Convert time to pressure then normalize
pb_1 = (p_sim_1 + (p_sim_2 - p_sim_1) * burst_time) / pb_ref_1;

% Fit the data using Buckingham pi theorem
h_norm = [2, 3.5, 5] / t;
l_norm = [2, 3.5, 5] / t;
a_norm = [1, 2.5, 4] / t;
[L, A, H] = meshgrid(l_norm, a_norm, h_norm);  % as in order x, y, z
H = reshape(H, [27, 1]);
L = reshape(L, [27, 1]);
A = reshape(A, [27, 1]);
tbl = table(H, A, L, pb_1);  % data from simulation is in reverse order
modelfun = @(c,x)1 + c(1)*(x(:,1).^c(2)).*(x(:,2).^c(3)).*(x(:,3).^c(4));
beta0 = [-1 1 0.1 -0.2];  % initial guess for the coeff
mdl = fitnlm(tbl,modelfun,beta0)  % do the fitting
fc = mdl.Coefficients{:,1};  % fitted coeff

if switch_1dplt
    % Plot the burst pressure as a function of a single parameter
    if strcmp(param, 'depth') % As a function of wall loss corrsion height
        for i = 1:4
            figure
            hold on
            for j = 2:5
                fix_param = [i, j]; % length, lig_2
                cols = find(length==fix_param(1) & ...
                            lig_2==fix_param(2));
                plot(depth(cols)/t, pb_1(cols),'-o', 'linewidth', 3, 'markersize', 20)
                fp = 1 + fc(1)*(depth(cols)/t).^fc(2).*(i/t)^fc(3).*(j/t)^fc(4);
                plot(depth(cols)/t, fp, '-ok', 'linewidth', 3, 'markersize', 20)
            end
            ylim([0.82, 0.95])
            box on 
            grid on
            xlabel('Normalized corrosion depth')
            ylabel('Normalized burst pressure')
            set(gca,'FontSize',40)
            set(gca,'YColor','k')
            set(gca,'LineWidth',2);
            set(gcf,'Units','Inches');
            set(gcf,'Position',[2 0.2 1.5*10. 1.37*7.5])
        end
    end

    if strcmp(param, 'length') % As a function of crack length
        for i = 2:5
            figure
            hold on
            for j = 2:5
                fix_param = [i, j]; % height, lig_2
                cols = find(depth==fix_param(1) & ...
                            lig_2==fix_param(2));
                plot(length(cols)/t, pb_1(cols),'-o', 'linewidth', 3, 'markersize', 20)
                fp = 1 + fc(1)*(i/t).^fc(2).*(length(cols)/t).^fc(3).*(j/t).^fc(4);
                plot(length(cols)/t, fp, '-ok', 'linewidth', 3, 'markersize', 20)
            end
            ylim([0.82, 0.95])
            box on
            grid on
            xlabel('Normalized crack length')
            ylabel('Normalized burst pressure')
            set(gca,'FontSize',40)
            set(gca,'YColor','k')
            set(gca,'LineWidth',2);
            set(gcf,'Units','Inches');
            set(gcf,'Position',[2 0.2 1.5*10. 1.37*7.5])
        end
    end

    if strcmp(param, 'lig') % As a function of ligament 2
        for i = 2:5
            figure
            hold on
            for j = 1:4
                fix_param = [i, j]; % height, length
                cols = find(depth==fix_param(1) & ...
                            length==fix_param(2));
                plot(lig_2(cols)/t, pb_1(cols),'-o', 'linewidth', 3, 'markersize', 20)
                fp = 1 + fc(1)*(i/t).^fc(2).*(j/t).^fc(3).*(lig_2(cols)/t).^fc(4);
                plot(lig_2(cols)/t, fp, '-ok', 'linewidth', 3, 'markersize', 20)
            end
            ylim([0.82, 0.95])
            box on
            grid on
            xlabel('Normalized ligament 2')
            ylabel('Normalized burst pressure')
            set(gca,'FontSize',40)
            set(gca,'YColor','k')
            set(gca,'LineWidth',2);
            set(gcf,'Units','Inches');
            set(gcf,'Position',[2 0.2 1.5*10. 1.37*7.5])
        end
    end
end

% Plot two variables at once
if switch_2dplt
    if strcmp(param, 'depth')
        [L, A] = meshgrid(l_norm, a_norm);
        figure
        for i = 2:5
            index = find(depth==i);
            pb = reshape(pb_1(index), [4,4])';
            surf(L, A, pb, 'FaceColor','interp')
            hold on
            fp = 1 + fc(1)*(i/t).^fc(2).*A.^fc(3).*L.^fc(4);
            plot3(L, A, fp', 'ko', 'linewidth', 2, 'markersize', 10)
        end
        xlabel('Normalized crack length')
        ylabel('Normalized ligament length')
        set(gca,'FontSize',30)
        set(gca,'YColor','k')
        set(gca,'LineWidth',2);
        set(gcf,'Units','Inches');
        set(gcf,'Position',[2 0.2 1.5*10. 1.37*7.5])
    end

    if strcmp(param, 'length')
        [L, H] = meshgrid(l_norm, h_norm);
        figure
        for i =  1:4
            index = find(length==i);
            pb = reshape(pb_1(index), [4,4])';
            surf(L, H, pb, 'FaceColor','interp')
            hold on
            fp = 1 + fc(1)*H.^fc(2).*(i/t).^fc(3).*L.^fc(4);
            plot3(L, H, fp, 'ko', 'linewidth', 2, 'markersize', 10)
        end
        xlabel('Normalized ligament length')
        ylabel('Normalized corrosion depth')
        set(gca,'FontSize',30)
        set(gca,'YColor','k')
        set(gca,'LineWidth',2);
        set(gcf,'Units','Inches');
        set(gcf,'Position',[2 0.2 1.5*10. 1.37*7.5])
    end

    if strcmp(param, 'lig')
        [A, H] = meshgrid(a_norm, h_norm);
        figure
        for i = 5:5
            index = find(lig_2==i);
            pb = reshape(pb_1(index), [4,4])';
            surf(A, H, pb, 'FaceColor','interp')
            hold on
            fp = 1 + fc(1)*H.^fc(2).*A.^fc(3).*(i/t).^fc(4);
            plot3(A, H, fp, 'ko', 'linewidth', 2, 'markersize', 10)
        end
        xlabel('Normalized crack length')
        ylabel('Normalized corrosion depth')
        set(gca,'FontSize',30)
        set(gca,'YColor','k')
        set(gca,'LineWidth',2);
        set(gcf,'Units','Inches');
        set(gcf,'Position',[2 0.2 1.5*10. 1.37*7.5])
    end
end

if switch_linplt
    % Do a linear plot after the dimensional analysis
    x = linspace(0, 1, 50);
    y = 1 + fc(1)*x;
    pb_x = H.^fc(2).*A.^fc(3).*L.^fc(4);
    figure
    hold on
    grid on
    box on
    plot(x,y,'k', 'linewidth', 3)
    plot(pb_x, pb_1, 'o', 'linewidth', 2, 'markersize', 10)
    legend('Linear fit', 'FEA data')
    xlabel('${(d/t)^{0.755}(a/t)^{0.226}(l/t)^{-0.483}}$','interpreter','latex')
    ylabel('Normalized burst pressure')
    set(gca,'FontSize',40)
    set(gca,'YColor','k')
    set(gca,'LineWidth',2);
    set(gcf,'Units','Inches');
    set(gcf,'Position',[2 0.2 1.5*10. 1.37*7.5])
end