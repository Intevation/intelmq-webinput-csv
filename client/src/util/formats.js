// Primitive patterns to detect whether a column could be a particular format

export const timestamp_regex = /^\d{4}-(?:0[1-9]|1[012])-(?:0[1-9]|[12]\d|3[01])(?:[T ][0-2]\d:[0-6]\d(?::[0-6]\d)?(?:[Z]|[+-]\d\d:?\d\d)?)?$/i;

export const ip_regex = /^(?:\d{1,3}(?:\.\d{1,3}){3}|[0-9a-f]{1,4}(?::[0-9a-f]{1,4}){7}|(?:[0-9a-f]{1,4}(?::[0-9a-f]{1,4}){0,6})?::(?:[0-9a-f]{1,4}(?::[0-9a-f]{1,4}){0,6})?)$/i;
