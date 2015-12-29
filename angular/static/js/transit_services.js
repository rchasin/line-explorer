var transitServices = angular.module('transitServices', [
    'ngResource',
]);

transitServices.factory('Agencies', ['$resource',
  function($resource) {
    return $resource('/api/agencies/');
  }
]);

transitServices.factory('Lines', ['$resource',
  function($resource) {
    return $resource('/api/lines/:agencyId');
  }
]);

transitServices.factory('Stops', ['$resource',
  function($resource) {
    return $resource('/api/stops/:agencyId/:lineId');
  }
]);
