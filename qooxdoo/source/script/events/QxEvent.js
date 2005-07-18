function QxEvent(eType, autoDispose)
{
  // if this object is not inherited and autoDispose is not explicitly
  // set to 'true' use default fallback 'false' - this differs from
  // the default behaviour of QxObject!
  if (typeof autoDispose != "boolean" && this.classname == "QxEvent") {
    autoDispose = false;
  };

  QxObject.call(this, autoDispose);

  if (isValid(eType)) {
    this._type = eType;
  };
};

QxEvent.extend(QxObject, "QxEvent");

proto._bubbles = false;
proto._propagationStopped = true;
proto._defaultPrevented = false;

proto._type = "";

proto._target = null;
proto._currentTarget = null;
proto._relatedTarget = null;



/*
  -------------------------------------------------------------------------------
    SETTER
  -------------------------------------------------------------------------------
*/

proto.setType = function(t) {
  this._type = t;
};

proto.setBubbles = function(b) {
  this._bubbles = b;
};

proto.setPropagationStopped = function(s) {
  this._propagationStopped = s;
};

proto.stopPropagation = function() {
  this._propagationStopped = true;
};

proto.setPreventDefault = function(d) {
  this._defaultPrevented = d;
};

proto.setTarget = function(t) {
  this._target = t;
};

proto.setCurrentTarget = function(t) {
  this._currentTarget = t;
};

proto.setRelatedTarget = function(t) {
  this._relatedTarget = t;
};

proto.preventDefault = function() {
  this.setPreventDefault(true);
};





/*
  -------------------------------------------------------------------------------
    GETTER
  -------------------------------------------------------------------------------
*/

proto.getType = function() {
  return this._type;
};

proto.getBubbles = function() {
  return this._bubbles;
};

proto.getPropagationStopped = function() {
  return this._propagationStopped;
};

proto.getPreventDefault = function() {
  return this._defaultPrevented;
};

proto.getTarget = function() {
  return this._target;
};

proto.getCurrentTarget = function() {
  return this._currentTarget;
};

proto.getRelatedTarget = function() {
  return this._relatedTarget;
};





/*
  -------------------------------------------------------------------------------
    DISPOSER
  -------------------------------------------------------------------------------
*/

proto.dispose = function()
{
  if(this._disposed) {
    return;
  };

  this._target = null;
  this._currentTarget = null;
  this._relatedTarget = null;

  QxObject.prototype.dispose.call(this);
};