var lineExplorerApp = angular.module('lineExplorerApp', [
    'ngRoute', 'transitServices', 'ui.bootstrap'
]);

lineExplorerApp.config([
    '$routeProvider',
    function ($routeProvider) {
        $routeProvider.
            otherwise({
                redirectTo: '/'
            });
    }]);

lineExplorerApp.controller('SearchBoxCtrl', [
  '$scope',
  'Agencies', 'Lines', 'Stops',
  function($scope, Agencies, Lines, Stops) {

    $scope.agencies = [];
    Agencies.get(function(response) {
      $scope.agencies = response.agencies;
    });

    $scope.agency = undefined; // controlled by input model
    $scope.lines = [];
    $scope.updateLines = function() {
      Lines.get({'agencyId': $scope.agency.id}, function(response) {
	$scope.lines = response.lines;
      });
    };
  }
]);
