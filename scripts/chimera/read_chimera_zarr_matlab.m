% Read Chimera matrices from a Zarr v3 store with zarr-matlab.
%
% Requires:
%   https://github.com/catalystneuro/zarr-matlab
%
% Install the toolbox, or add the cloned zarr-matlab folder to the MATLAB path
% before running this script.

clearvars

% Public read-only HTTP store. For cluster-local reads, use the local path below.
chimeraStore = 'http://meteo.unican.es/work/chimera.zarr';
% chimeraStore = '/lustre/gmeteo/WORK/WWW/chimera.zarr';

nVars = 5;
firstMatrixId = 0;   % Chimera IDs are zero-based.
nMatrices = 10;

arrayName = ['matrices' num2str(nVars)];

if startsWith(chimeraStore, 'http://') || startsWith(chimeraStore, 'https://')
    % zarr-matlab needs an explicit HttpStore object for remote stores.
    % HTTP stores are not listable, so open the array by Path.
    store = zarr.stores.HttpStore(chimeraStore);
    matrices = zarr.open(store, 'Path', arrayName);
else
    matrices = zarr.open(chimeraStore, 'Path', arrayName);
end

fprintf('Opened %s/%s\n', chimeraStore, arrayName);
disp(matrices)

% Option 1: read by Chimera ID using zarr-matlab's read API.
% Chimera IDs are zero-based, but zarr-matlab uses MATLAB-style one-based
% coordinates here.
block = matrices.read([firstMatrixId + 1 1 1], [nMatrices nVars nVars]);

fprintf('Read %d matrices starting at Chimera ID %d\n', nMatrices, firstMatrixId);
disp(size(block))

% Option 2: MATLAB-style indexing. MATLAB indices are one-based, so add 1 to
% Chimera's zero-based matrix ID.
firstMatlabIndex = firstMatrixId + 1;
lastMatlabIndex = firstMatlabIndex + nMatrices - 1;
block2 = matrices(firstMatlabIndex:lastMatlabIndex, :, :);

fprintf('The two access methods return the same data: %d\n', isequal(block, block2));

% Show one matrix as a normal 2-D MATLAB array.
oneMatrix = squeeze(block(1,:,:));
disp(oneMatrix)
