ObjC.import('Foundation');
function run(argv) {
  if (argv.length !== 1) throw new Error('Chemin du projet requis');
  function read(p) { return ObjC.unwrap($.NSString.stringWithContentsOfFileEncodingError($(p), $.NSUTF8StringEncoding, null)); }
  eval(read(argv[0] + '/site/core.js'));
  var config = JSON.parse(read(argv[0] + '/site/config.json'));
  var count = 0;
  ['macbook-pro', 'mac-mini'].forEach(function (profile) {
    JarvisCore.actions.forEach(function (action) { JarvisCore.planFromURL(config, JarvisCore.buildURL(profile, action), profile, profile); count++; });
  });
  var rejected = false;
  try { JarvisCore.parseURL('jarvis-launcher://launch/mac-mini/ssh?command=id'); } catch (_) { rejected = true; }
  if (!rejected) throw new Error('Injection non rejetée');
  return 'GO politique JXA : ' + count + ' plans valides et URL arbitraire refusée. Ceci ne valide pas Terminal ou SSH.';
}
