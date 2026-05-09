// Code moved from
// https://github.com/Intevation/intelmq-webinput-csv/blob/6f9444fa92e99e0a7130bc196fb3d8c449eff2ad/client/src/components/WebinputCSV.vue#L1399
export const parseMIME = mime => {
  const parts = mime.split('\n');
  let isHeader = true;
  let isMimeHeader = false;
  let isBody = false;
  let line;
  let subject;
  let to;
  let body = '';
  let previousHeader;
  let contentType;  // either 'multipart/signed' or 'text/plain'
  let contentCharset = 'utf-8';  // utf-8 is the current default of mailgen, we can assume it as default and fallback
  for (var lineindex = 0; lineindex < parts.length; lineindex++) {
    line = parts[lineindex];
    if (isHeader) {
      //console.log(line, 'is header');
      if (line == '\r') {
        //console.log('ends header');
        isHeader = false;
        if (contentType == 'text/plain') {
          // for plain text messages, this is the start of the body. For MIME messages, we need to detect the MIME header first
          isBody = true;
        }
      } else if (line.split(':')[0] == 'Subject') {
        //console.log('is subject');
        subject = line.slice(9);
        previousHeader = 'subject';
      } else if (line.split(':')[0] == 'To') {
        //console.log('is to');
        to = line.slice(4);
        previousHeader = 'to';
      } else if (line.split(':')[0] == 'Content-Type') {
        contentType = line.split(' ')[1].replace(';', '');
        //console.log('is content type', contentType);
        if (contentType == 'text/plain') {
          // extract the content-type
          let parsed = line.match(/^Content-Type:.*?charset="(.*?)"/);
          if (parsed !== null) {
            //console.log('parsed line for charset detection', parsed);
            contentCharset = parsed[1];
          }
        }
      } else if (line.slice(0, 1) == ' ' && previousHeader !== undefined) {
        //console.log('is continuation of', previousHeader);
        switch (previousHeader) {
          case 'subject':
            subject = subject + ' ' + line.slice(1);
            break;
          case 'to':
            to = to + ' ' + line.slice(1);
            break;
        }
      } else {
        previousHeader = undefined;
      }
    } else if (isMimeHeader) {
      if (line == '\r') {
        //console.log(line, 'starts MIME part body');
        isMimeHeader = false;
        isBody = true;
      } else {
        //console.log(line, 'is MIME header');
        // extract the content-type
        let parsed = line.match(/^Content-Type:.*?charset="(.*?)"/);
        if (parsed !== null) {
          //console.log('parsed line for charset detection', parsed);
          contentCharset = parsed[1];
        }
        parsed = line.match(/Content-Type: *?application\/pgp-signature/);
        if (parsed !== null) {
          //console.log('MIME part is PGP Signature, ignore it');
          isBody = false;
          isMimeHeader = false;
        }
      }
    } else if (!isBody && contentType == 'multipart/signed') {
      if (line.slice(0, 17) == '--===============') {
        //console.log(line, 'is MIME part start');
        isMimeHeader = true;
      }
    } else if (isBody) {
      //console.log(line, 'is Body');
      if (contentType == 'multipart/signed') {
        if (line.slice(0, 17) == '--===============') {
          isBody = false;
          isMimeHeader = true;
        } else {
          body += line + '\n';
        }
      } else {
        body += line + '\n';
      }
    }
  }

  // https://stackoverflow.com/a/75475328/2851664
  // CC BY-SA https://stackoverflow.com/users/15702521/lukas
  const dc = new TextDecoder(contentCharset);
  let decodedBody = body.replace(/[\t\x20]$/gm, "").replace(/=(?:\r\n?|\n)/g, "").replace(/((?:=[a-fA-F0-9]{2})+)/g, (m) => {
    const cd = m.substring(1).split('='), uArr=new Uint8Array(cd.length);
    for (let i = 0; i < cd.length; i++) {
      uArr[i] = parseInt(cd[i], 16);
    }
    return dc.decode(uArr);
  });

  return [subject, to, decodedBody, contentType];
};
