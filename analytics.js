/* Sihtak: privacy-first website analytics (Azure Application Insights)
   ----------------------------------------------------------------------------
   Feeds Ops Central, alongside the existing Google Analytics tag. Same approach
   as catenix.com/analytics.js and labsyria.com: cookieless by design
   (disableCookiesUsage writes nothing to cookies or localStorage and stores no
   cross-session identifier on the device), Do-Not-Track respected, no session
   replay, hosted in West Europe.

   GA4 (G-JGTTBKMM4G) is deliberately left in place. It holds the history; this
   is what Ops Central can read without a Google login.

   NOTE: staticwebapp.config.json carries a Content-Security-Policy. This file
   only works because script-src allows js.monitor.azure.com and connect-src
   allows the ingestion endpoint. If either is removed, telemetry stops silently.

   External file ON PURPOSE: the sibling labsyria.com site shipped the Microsoft
   minified snippet inline, one dropped ")" made the block unparseable, and it
   recorded zero traffic for a week before anyone noticed. */
(function () {
  var IKEY = 'f5ec237c-a410-4871-9338-0f530110c1e8';
  var INGEST = 'https://westeurope-5.in.applicationinsights.azure.com';
  var CONNECTION_STRING = 'InstrumentationKey=' + IKEY +
    ';IngestionEndpoint=' + INGEST + '/' +
    ';LiveEndpoint=https://westeurope.livediagnostics.monitor.azure.com/' +
    ';ApplicationId=7931d716-401d-4305-9dad-5b494cc6070e';

  if (navigator.doNotTrack === '1' || window.doNotTrack === '1' || navigator.msDoNotTrack === '1') { return; }

  // No telemetry from local or dev copies.
  var HOSTS = ['sihtak.com', 'www.sihtak.com'];
  if (HOSTS.indexOf(location.hostname) === -1) { return; }

  var sent = false;

  /* Fallback beacon. A large share of the audience is in the Middle East and
     North Africa, where the Azure CDN that hosts the SDK can be slow or
     blocked. If the SDK never loads we would silently count nobody, so post one
     minimal pageview straight to the ingestion endpoint instead. Marked
     fallback:"1" so it is distinguishable from full SDK telemetry. */
  function fallbackPageView() {
    if (sent) { return; }
    sent = true;
    try {
      var envelope = {
        name: 'Microsoft.ApplicationInsights.' + IKEY.replace(/-/g, '') + '.Pageview',
        time: new Date().toISOString(),
        iKey: IKEY,
        tags: {
          'ai.device.type': 'Browser',
          'ai.operation.name': location.pathname || '/',
          'ai.internal.sdkVersion': 'sihtak-fallback:1'
        },
        data: {
          baseType: 'PageviewData',
          baseData: {
            ver: 2,
            name: (document.title || '').slice(0, 200),
            url: location.href,
            properties: { refUri: document.referrer || '(direct)', fallback: '1' }
          }
        }
      };
      fetch(INGEST + '/v2/track', {
        method: 'POST',
        body: JSON.stringify(envelope),
        mode: 'cors',
        keepalive: true
      })['catch'](function () { /* offline or blocked: nothing more we can do */ });
    } catch (e) { /* analytics must never break the page */ }
  }

  var s = document.createElement('script');
  s.src = 'https://js.monitor.azure.com/scripts/b/ai.3.gbl.min.js';
  s.async = true;
  s.crossOrigin = 'anonymous';

  s.onerror = fallbackPageView;

  s.onload = function () {
    try {
      var ai = new window.Microsoft.ApplicationInsights.ApplicationInsights({
        config: {
          connectionString: CONNECTION_STRING,
          disableCookiesUsage: true,        // cookieless: no cookies, no localStorage
          disableAjaxTracking: true,
          disableFetchTracking: true,       // do not touch the fahsak-api calls
          enableAutoRouteTracking: false,   // static site: one page view per load
          autoTrackPageVisitTime: true,
          disableExceptionTracking: false,
          enableUnhandledPromiseRejectionTracking: false
        }
      });
      ai.loadAppInsights();
      ai.trackPageView();
      sent = true;
      window.sihtakAI = ai;
    } catch (e) {
      fallbackPageView();
    }
  };

  document.head.appendChild(s);

  // If the SDK has not reported within 8s (blocked, throttled, hung), count the visit anyway.
  setTimeout(fallbackPageView, 8000);
})();
