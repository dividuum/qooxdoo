/* ************************************************************************

   qooxdoo - the new era of web interface development

   Copyright:
     (C) 2004-2006 by Schlund + Partner AG, Germany
         All rights reserved

   License:
     LGPL 2.1: http://creativecommons.org/licenses/LGPL/2.1/

   Internet:
     * http://qooxdoo.oss.schlund.de

   Authors:
     * Sebastian Werner (wpbasti)
       <sebastian dot werner at 1und1 dot de>
     * Andreas Ecker (aecker)
       <andreas dot ecker at 1und1 dot de>

************************************************************************ */

/* ************************************************************************

#package(core)
#use(qx.util.Validation)
#use(qx.event.type.Event)
#use(qx.event.type.DataEvent)

************************************************************************ */


/*!
This is the main constructor for all objects that need to be connected to qx.event.type.Event objects.

In objects created with this constructor, you find functions to addEventListener or
removeEventListener to or from the created object. Each event to connect to has a type in
form of an identification string. This type could be the name of a regular dom event like qx.Const.EVENT_TYPE_CLICK or
something self-defined like "ready".
*/
qx.OO.defineClass("qx.core.Target", qx.core.Object,
function(vAutoDispose) {
  qx.core.Object.call(this, vAutoDispose);
});

qx.Class.EVENTPREFIX = "evt";




/*
---------------------------------------------------------------------------
  EVENT CONNECTION
---------------------------------------------------------------------------
*/

/*!
  Add event listener to object
*/
qx.Proto.addEventListener = function(vType, vFunction, vObject)
{
  if(this._disposed) {
    return;
  };

  if(typeof vFunction !== qx.Const.TYPEOF_FUNCTION) {
    throw new Error("qx.core.Target: addEventListener(" + vType + "): '" + vFunction + "' is not a function!");
  };

  // If this is the first event of given type, we need to create a subobject
  // that contains all the actions that will be assigned to this type
  if (typeof this._listeners === qx.Const.TYPEOF_UNDEFINED)
  {
    this._listeners = {};
    this._listeners[vType] = {};
  }
  else if(typeof this._listeners[vType] === qx.Const.TYPEOF_UNDEFINED)
  {
    this._listeners[vType] = {};
  };

  // Create a special vKey string to allow identification of each bound action
  var vKey = qx.core.Target.EVENTPREFIX + qx.core.Object.toHashCode(vFunction) + (vObject ? qx.constant.Core.UNDERLINE + qx.core.Object.toHashCode(vObject) : qx.constant.Core.EMPTY);

  // Finally set up the listeners object
  this._listeners[vType][vKey] =
  {
    handler : vFunction,
    object : vObject
  };
};

/*!
  Remove event listener from object
*/
qx.Proto.removeEventListener = function(vType, vFunction, vObject)
{
  if(this._disposed) {
    return;
  };

  var vListeners = this._listeners;
  if (!vListeners || typeof vListeners[vType] === qx.Const.TYPEOF_UNDEFINED) {
    return;
  };

  if(typeof vFunction !== qx.Const.TYPEOF_FUNCTION) {
    throw new Error("qx.core.Target: removeEventListener(" + vType + "): '" + vFunction + "' is not a function!");
  };

  // Create a special vKey string to allow identification of each bound action
  var vKey = qx.core.Target.EVENTPREFIX + qx.core.Object.toHashCode(vFunction) + (vObject ? qx.constant.Core.UNDERLINE + qx.core.Object.toHashCode(vObject) : qx.constant.Core.EMPTY);

  // Delete object entry for this action
  delete this._listeners[vType][vKey];
};








/*
---------------------------------------------------------------------------
  EVENT CONNECTION UTILITIES
---------------------------------------------------------------------------
*/

/*!
  Check if there are one or more listeners for an event type
*/
qx.Proto.hasEventListeners = function(vType) {
  return this._listeners && typeof this._listeners[vType] !== qx.Const.TYPEOF_UNDEFINED && !qx.lang.Object.isEmpty(this._listeners[vType]);
};

/*!
  Checks if the event is registered. If so it creates a event object and dispatch it.
*/
qx.Proto.createDispatchEvent = function(vType)
{
  if (this.hasEventListeners(vType)) {
    this.dispatchEvent(new qx.event.type.Event(vType), true);
  };
};

/*!
  Checks if the event is registered. If so it creates a data event object and dispatch it.
*/
qx.Proto.createDispatchDataEvent = function(vType, vData)
{
  if (this.hasEventListeners(vType)) {
    this.dispatchEvent(new qx.event.type.DataEvent(vType, vData), true);
  };
};








/*
---------------------------------------------------------------------------
  EVENT DISPATCH
---------------------------------------------------------------------------
*/

/*!
  Public dispatch implementation
*/
qx.Proto.dispatchEvent = function(vEvent, vEnableDispose)
{
  // Ignore event if eventTarget is disposed
  if(this.getDisposed()) {
    return;
  };

  if (vEvent.getTarget() == null) {
    vEvent.setTarget(this);
  };

  if (vEvent.getCurrentTarget() == null) {
    vEvent.setCurrentTarget(this);
  };

  // Dispatch Event
  this._dispatchEvent(vEvent, vEnableDispose);

  return !vEvent._defaultPrevented;
};

/*!
  Internal dispatch implementation
*/
qx.Proto._dispatchEvent = function(vEvent, vEnableDispose)
{
  if(this.getDisposed()) {
    return;
  };

  var vListeners = this._listeners;
  if (vListeners)
  {
    // Setup current target
    vEvent.setCurrentTarget(this);

    // Shortcut for listener data
    var vTypeListeners = vListeners[vEvent.getType()];

    if(vTypeListeners)
    {
      var vFunction, vObject;

      // Handle all events for the specified type
      for (var vHashCode in vTypeListeners)
      {
        // Shortcuts for handler and object
        vFunction = vTypeListeners[vHashCode].handler;
        vObject = vTypeListeners[vHashCode].object;

        // Call object function
        try
        {
          if(typeof vFunction === qx.Const.TYPEOF_FUNCTION) {
            vFunction.call(qx.util.Validation.isValid(vObject) ? vObject : this, vEvent);
          };
        }
        catch(ex)
        {
          this.error("Could not dispatch event of type \"" + vEvent.getType() + "\"", ex);
        };
      };
    };
  };

  // Bubble event to parents
  var vParent = this.getParent();
  if(vEvent.getBubbles() && !vEvent.getPropagationStopped() && vParent && !vParent.getDisposed() && vParent.getEnabled()) {
    vParent._dispatchEvent(vEvent, false);
  };

  // vEnableDispose event?
  vEnableDispose && vEvent.dispose();
};

/*!
  Internal placeholder for bubbling phase of an event.
*/
qx.Proto.getParent = function() {
  return null;
};






/*
---------------------------------------------------------------------------
  DISPOSER
---------------------------------------------------------------------------
*/

qx.Proto.dispose = function()
{
  if(this.getDisposed()) {
    return;
  };

  if (typeof this._listeners === qx.Const.TYPEOF_OBJECT)
  {
    for (var vType in this._listeners)
    {
      for (var vKey in this._listeners[vType])
      {
        this._listeners[vType][vKey] = null;
        delete this._listeners[vType][vKey];
      };

      this._listeners[vType] = null;
      delete this._listeners[vType];
    };
  };

  this._listeners = null;
  delete this._listeners;

  return qx.core.Object.prototype.dispose.call(this);
};
