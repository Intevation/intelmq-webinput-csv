<template>
  <div>
    <b-navbar toggleable="lg" type="dark" variant="info">
      <b-navbar-brand href="#">IntelMQ - Webinput CSV</b-navbar-brand>
      <b-navbar-nav v-if="hasAuth" class="ml-auto">
        <b-button v-if="!loggedIn" v-b-modal.login-popup size="sm" class="my-2 my-sm-0" type="submit">Login</b-button>
        <b-button v-if="loggedIn" size="sm" class="my-2 my-sm-0" @click="signOut">Logout</b-button>
      </b-navbar-nav>
    </b-navbar>
    <div>
      <b-modal v-model="showLogin" id="login-popup" title="IntelMQ - Webinput-CSV - Sign in">
        <label v-if="wrongCredentials" class="text-danger">{{ loginErrorText }}</label>
        <b-form>
          <div>
            <label for="username">Username</label>
            <b-form-input v-model="username" type="text" id="username"  placeholder="Name" @keyup.enter="signIn"></b-form-input>
            <label for="password">Password</label>
            <b-form-input v-model="password" type="password" id="password"  placeholder="Password" @keyup.enter="signIn"></b-form-input>
          </div>
        </b-form>
        <template #modal-footer>
            <b-button
              variant="primary"
              size="sm"
              class="float-right"
              @click="signIn"
            >
              Login
            </b-button>
        </template>
      </b-modal>
      <b-modal v-model="showAuthConfirm" id="authconfirm-popup" title="Confirm Authentication for Submission">
        <label v-if="authConfirmErrorText" class="text-danger">{{ authConfirmErrorText }}</label>
        <b-form>
          <div>
            <label for="username">Username</label>
            <b-form-input v-model="username" type="text" id="username"  placeholder="Name"></b-form-input>
            <label for="password">Password</label>
            <b-form-input v-model="password" type="password" id="password"  placeholder="Password"></b-form-input>
          </div>
        </b-form>
        <template #modal-footer>
            <b-button
              variant="primary"
              size="sm"
              class="float-right"
              @click="sendData(submit=true);"
            >
              Submit
            </b-button>
        </template>
      </b-modal>
      <b-modal v-model="showMailgenLog" scrollable centered size="xl" id="mailgenLog-popup" title="Mailgen Log">
        <code class="text-black"><pre>{{ mailgenLog }}</pre></code>
        <template #modal-footer>
          <b-button
            variant="primary"
            class="float-right"
            @click="showMailgenLog=false"
          >
            Close
          </b-button>
        </template>
      </b-modal>
      <b-modal v-model="showMailgenPreview" scrollable centered size="xl" id="mailgenPreview-popup" title="Mailgen Email Preview">
        <h4 title="Subject">{{mailgenPreviewParsed.subject}}</h4>
        <code class="text-black"><pre>{{ mailgenPreviewParsed.body }}</pre></code>
        <template #modal-footer>
          <b-button
            variant="secondary"
            class="float-right"
            @click="showMailgenPreviewRaw=true"
          >
            Show Raw
          </b-button>
          <b-button
            variant="primary"
            class="float-right"
            @click="showMailgenPreview=false"
          >
            Close
          </b-button>
        </template>
      </b-modal>
      <b-modal v-model="showMailgenPreviewRaw" scrollable centered size="xl" id="mailgenPreviewRaw-popup" title="Mailgen Raw Email">
        <code class="text-black"><pre>{{ mailgenPreview }}</pre></code>
        <template #modal-footer>
          <b-button
            variant="primary"
            class="float-right"
            @click="showMailgenPreviewRaw=false"
          >
            Close
          </b-button>
        </template>
      </b-modal>
      <b-modal
        v-model="showErrorModal"
        title="Error"
        scrollable
        size="xl"
        ok-only>
        <p>Error message:</p>
        <code><pre>{{errorMessage}}</pre></code>
      </b-modal>
    </div>
    <div v-if="loggedIn">
      <div class="accordion" role="tablist">
        <b-overlay :show="overlay" opacity="0.5" @shown="parseCSV">
          <b-card no-body class="mb-1">
            <b-card-header header-tag="header" class="p-1" role="tab">
              <b-button block v-b-toggle.accordion-1 variant="info">CSV Content</b-button>
            </b-card-header>
            <b-collapse id="accordion-1" visible accordion="my-accordion" role="tabpanel">
              <b-card-body>
                <b-container fluid>
                  <b-row>
                    <b-col cols="11">
                      <b-form-group >
                        <b-form-file
                          v-model="csvFile"
                          placeholder="Choose a file or drop it here..."
                          drop-placeholder="Drop file here..."
                          @input="readFromFile"
                        ></b-form-file>
                      </b-form-group>
                    </b-col>
                    <b-col>
                      <b-button @click="reset">Clear</b-button>
                    </b-col>
                  </b-row>
                </b-container>
                <b-container fluid>
                  <b-form-group >
                    <b-form-textarea
                      v-if="!csvFile"
                      id="textarea"
                      v-model="csvText"
                      placeholder="Or paste CSV data here"
                      rows="5"
                      @change="parseCSV"
                    ></b-form-textarea>
                    <b-form-textarea
                      v-if="!!csvFile"
                      id="textareaPreview"
                      v-model="csvPreviewText"
                      rows="5"
                    ></b-form-textarea>
                  </b-form-group>
                </b-container>
                <b-container fluid>
                  <b-row>
                    <b-col>
                      <b-form-group label-cols=7 label="Delimiter">
                        <b-form-select
                          v-model="delimiter"
                          :options="delimiterOptions"
                          @change="showOverlay"
                        ></b-form-select>
                      </b-form-group>
                    </b-col>
                    <b-col>
                      <b-form-group label-cols=7 label="Quote char">
                        <b-form-input
                          v-model="quoteChar"
                          type="text"
                          placeholder='"'
                          @change="showOverlay"
                        ></b-form-input>
                      </b-form-group>
                    </b-col>
                    <b-col>
                      <b-form-group label-cols=7 label="Escape char">
                        <b-form-input
                          v-model="escapeChar"
                          type="text"
                          placeholder="\"
                          @change="showOverlay"
                        ></b-form-input>
                      </b-form-group>
                    </b-col>
                    <b-col>
                      <b-form-group label-cols=7 label="Has Header">
                        <b-form-checkbox
                          v-model="hasHeader"
                          @change="showOverlay"
                        ></b-form-checkbox>
                      </b-form-group>
                    </b-col>
                    <b-col>
                      <b-form-group id="option1" label-cols=9 label="Skip initial Whitespace">
                        <b-form-checkbox
                          v-model="initialWhitespace"
                          @change="showOverlay"
                        ></b-form-checkbox>
                      </b-form-group>
                      <b-tooltip target="option1" triggers="hover">
                        When True, whitespace immediately following the delimiter is ignored.
                      </b-tooltip>
                    </b-col>
                    <b-col>
                      <b-form-group id="option2" label-cols=7 label="Skip initial N lines">
                        <b-form-input
                          v-model="skipLines"
                          type="number"
                          @change="showOverlay"
                        ></b-form-input>
                      </b-form-group>
                      <b-tooltip target="option2" triggers="hover">
                        Skip initial N lines after the header.
                      </b-tooltip>
                    </b-col>
                  </b-row>
                </b-container>
              </b-card-body>
            </b-collapse>
          </b-card>
        </b-overlay>

        <b-card no-body class="mb-1">
          <b-card-header header-tag="header" class="p-1" role="tab">
            <b-button :disabled="!csvFile && csvText === ''" block v-b-toggle.accordion-3 variant="info">Data Validation and Submission</b-button>
          </b-card-header>
          <b-collapse id="accordion-3" accordion="my-accordion" role="tabpanel">
            <b-card-body>
              <b-container fluid>
                <b-row>
                  <b-col>
                    <label>CSV Parsing Result: {{ lines }} lines, {{ errors }} errors</label>
                    <b-form-group label-cols=4 label="Timezone">
                      <b-form-select
                        v-model="timezone"
                        :options="timezones"
                      ></b-form-select>
                    </b-form-group>
                    <b-form-group v-b-tooltip.hover label-cols=4 label="Dryrun" title="Override the values of Classification Type and Classification Identifier to 'test'.">
                      <b-form-checkbox
                        v-model="dryrun"
                        switch
                      ></b-form-checkbox>
                    </b-form-group>
                    <b-form-group v-b-tooltip.hover label-cols=4 label="Validate with bots" title="Validate the data with all configured IntelMQ Bots included.">
                      <b-form-checkbox
                        v-model="validateWithBots"
                        switch
                        :disabled="!botsAvailable.status"
                        :title="botsAvailable.reason"
                      ></b-form-checkbox>
                    </b-form-group>
                    <b-form-group
                      :label="mailgenAvailableTargetGroups.tag_name"
                      label-cols=4
                      v-if="mailgenAvailable">
                      <b-form-checkbox-group
                        v-model="mailgenTargetGroups"
                        :options="mailgenAvailableTargetGroups.tag_values"
                        v-if="mailgenAvailableTargetGroupsStatus === true && mailgenAvailableTargetGroups.tag_values && mailgenAvailableTargetGroups.tag_values.length"
                      ></b-form-checkbox-group>
                      <span
                        v-if="mailgenAvailableTargetGroupsStatus === null || (mailgenAvailableTargetGroups.tag_values && mailgenAvailableTargetGroups.tag_values.length == 0)"
                        >None defined
                      </span>
                      <span
                        class="text-danger"
                        v-else-if="mailgenAvailableTargetGroupsStatus !== true"
                        >Error: {{ mailgenAvailableTargetGroupsStatus }}
                      </span>
                    </b-form-group>
                    <b-container>
                      <b-row>
                        <b-col>
                          <b-overlay
                            :show="inProgress"
                            rounded
                            opacity="0.5"
                            spinner-small
                            spinner-variant="primary"
                            class="d-inline-block"
                          >
                            <b-button @click="sendData(submit=false)" variant="info">Validate data</b-button>
                          </b-overlay>
                        </b-col>
                        <b-col>
                          <b-overlay
                            :show="inProgress"
                            rounded
                            opacity="0.5"
                            spinner-small
                            spinner-variant="primary"
                            class="d-inline-block"
                          >
                            <b-button @click="onSendData" variant="primary">Send data</b-button>
                          </b-overlay>
                        </b-col>
                        <b-col>
                          <b-overlay
                            :show="inProgress"
                            rounded
                            opacity="0.5"
                            spinner-small
                            spinner-variant="primary"
                            class="d-inline-block"
                          >
                            <label style="margin-left: 10px;" :class="transferStatus">{{ transferred }}</label><br />
                          </b-overlay>
                        </b-col>
                      </b-row>
                      <b-row>
                        <b-col>
                          <label v-b-tooltip.hover title="These fields need to be present in the data. Data lines not containing them will not be submitted. Can be configured by the server administrator in the configuration.">
                            Required fields:
                            <span v-for="(field, index) in requiredFields" :key="index" style="margin-right: 3px">
                              <span v-if="index !== 0">, </span>
                              <code>{{ field }}</code>
                            </span>
                            <span v-if="!requiredFields.length">None</span>
                          </label>
                        </b-col>
                      </b-row>
                    </b-container>
                  </b-col>
                  <b-col>
                    <h4>Constant fields (fallback values)</h4>
                    <b-form-group label-cols=4 label="classification type">
                      <b-form-select
                        v-model="classificationType"
                        :options="classificationTypes"
                      ></b-form-select>
                    </b-form-group>
                    <b-form-group v-for="field in customFieldsMapping" :key="field.key" :id="field.key" label-cols=4 :label="field.key" label-class="text-monospace">
                      <b-form-input v-model="field.value" type="text"></b-form-input>
                    </b-form-group>
                  </b-col>
                </b-row>
              </b-container>
              <b-table sticky-header="600px"
                ref="table"
                striped
                bordered
                :current-page="currentPage"
                :per-page="perPage"
                :fields="tableHeader"
                :items="tableData"
              >
                <template #head()="data">
                  <span class="text-info">{{ data.label }}</span>
                  <v-select
                    :id="data.label"
                    :value="data.field"
                    :options="harmonizationFields"
                    v-if="data.label != 'Actions'"
                    taggable
                    @input="(fieldname) => update(data.field, fieldname)"
                  ></v-select>
                </template>
                <template #cell(Actions)="row">
                  #{{ row.index + 1 }}
                  <b-overlay
                            :show="rowModalInProgress"
                            rounded
                            opacity="0.5"
                            spinner-small
                            spinner-variant="primary"
                            class="d-inline-block"
                          >
                    <b-button
                      size="sm"
                      @click="triggerShowRowModal(row)"
                      variant="info"
                    >Show Processed Row</b-button>
                  </b-overlay>
                </template>
                <template #cell()="row">
                  <div :class="getTableCellClass(row)">
                    <span v-b-tooltip.hover :title="getTooltip(row.index, row.field.key)">{{row.value}}</span>
                  </div>
                </template>
                <template #foot(name)="data">
                  <span class="text-danger">{{ data.label }}</span>
                </template>
                <template #foot()="data">
                  <i>{{ data.label }}</i>
                </template>
              </b-table>
              <b-modal
                v-model="showRowModal"
                title="Processed Row Data"
                scrollable
                size="xl"
                ok-only>
                <div v-if="rowModalData.notifications">
                  <p>Notifications:</p>
                  <code><pre>{{rowModalData.notifications}}</pre></code>
                </div>
                <div v-if="rowModalData.messages">
                  <p>Messages ({{rowModalData.messages.length}}) after processing by bots (excluding output bots):</p>
                  <code><pre>{{rowModalData.messages}}</pre></code>
                </div>
                <div v-if="rowModalData.log">
                  <p>Log:</p>
                  <code><pre>{{rowModalData.log}}</pre></code>
                </div>
              </b-modal>
              <b-container>
                <b-row>
                  <b-col>
                    <b-form-group
                      label="Per page"
                      label-for="per-page-select"
                      label-cols="6"
                      label-size="sm"
                      class="mb-0"
                    >
                      <b-form-select
                        id="per-page-select"
                        v-model="perPage"
                        :options="pageOptions"
                        size="sm"
                      ></b-form-select>
                    </b-form-group>
                  </b-col>
                  <b-col>
                    <b-pagination
                      v-model="currentPage"
                      :total-rows="lines"
                      :per-page="perPage"
                      align="fill"
                      size="sm"
                      class="my-0"
                    ></b-pagination>
                  </b-col>
                </b-row>
              </b-container>
            </b-card-body>
          </b-collapse>
        </b-card>
        <b-card no-body class="mb-1">

          <b-card-header header-tag="header" class="p-1" role="tab">
            <b-button :disabled="!mailgenAvailable" block v-b-toggle.accordion-notifications variant="info" :title="mailgenAvailable ? 'Mailgen Template' : 'Mailgen is not installed/available'">Send Notifications</b-button>
          </b-card-header>
          <b-collapse id="accordion-notifications" visible accordion="my-accordion" role="tabpanel">
            <b-card-body>
              <b-container fluid>
                <b-row>
                  <b-col sm="auto">
                    <b-container fluid>
                      <b-row class=".align-items-center .justify-content-center">
                        <b-col>
                          <b-overlay
                            :show="mailgenInProgress"
                            rounded
                            opacity="0.5"
                            spinner-small
                            spinner-variant="primary"
                            class="d-inline-block"
                          >
                            <b-button v-b-tooltip.hover @click="runMailgen" variant="primary" :disabled="!mailgenAvailable" :title="mailgenAvailable ? 'Start Mailgen' : 'Mailgen is not installed/available'">Start Mailgen</b-button>
                          </b-overlay>
                        </b-col>
                        <b-col>
                          <b-overlay
                            :show="mailgenInProgress"
                            rounded
                            opacity="0.5"
                            spinner-small
                            spinner-variant="primary"
                            class="d-inline-block"
                          >
                            <b-button v-b-tooltip.hover @click="previewMailgen" variant="primary" :disabled="!mailgenAvailable" :title="mailgenAvailable ? 'Preview Mailgen Email' : 'Mailgen is not installed/available'">Email Preview</b-button>
                          </b-overlay>
                        </b-col>
                      </b-row>
                      <b-row>
                        <b-col>
                          <b-form-group label-cols=12 label="Verbose Logs:">
                            <b-form-checkbox
                              v-model="mailgenVerbose"
                            ></b-form-checkbox>
                          </b-form-group>
                        </b-col>
                        <b-col>
                          <b-form-group label-cols=6 label="Simulate:" title="Do not send notifications">
                            <a href="http://intevation.github.io/intelmq-mailgen/intelmqcbmail.html#dry-run-simulation" target="_blank">?</a>
                            <b-form-checkbox
                              v-model="mailgenDryRun"
                            ></b-form-checkbox>
                          </b-form-group>
                        </b-col>
                      </b-row>
                      <b-row>
                        <b-col>
                          <b-overlay
                            :show="mailgenInProgress"
                            rounded
                            opacity="0.5"
                            spinner-small
                            spinner-variant="primary"
                            class="d-inline-block"
                          >
                            <label style="margin-left: 10px;" :class="mailgenStatus">{{ mailgenResult }}</label><br />
                            <b-button @click="showMailgenLog=true" v-b-modal.mailgenLog-popup v-if="mailgenLog && mailgenLog != mailgenResult">Show complete log</b-button>
                          </b-overlay>
                        </b-col>
                      </b-row>
                      <b-row>
                        <b-col v-if="mailgenPreview">
                          <b-overlay
                            :show="mailgenInProgress"
                            rounded
                            opacity="0.5"
                            spinner-small
                            spinner-variant="primary"
                            class="d-inline-block"
                          >
                            <b-button @click="showMailgenPreview=true" v-b-modal.mailgenPreview-popup v-if="mailgenPreview">Show Email Preview</b-button>
                          </b-overlay>
                        </b-col>
                      </b-row>
                    </b-container>
                  </b-col>
                  <b-col>
                    <h4>Notification Template</h4>
                    <b-form-group width="100%">
                      <b-form-textarea
                        id="template"
                        v-model="template"
                        description="E-Mail Template for Mailgen. First line is the subject. Use ${fieldname} to insert aggregated field names and ${events_as_csv} for a CSV attachment."
                        rows="10"
                        width="100%"
                      ></b-form-textarea>
                    </b-form-group>
                  </b-col>
                </b-row>
                <h4>Templates:</h4>
                <b-row v-for="(item, index) in templates" v-bind:key="index" class="item">
                  <b-col>
                    <b-form-group
                      label="Template name"
                      description="With an empty name, the template will be ignored"
                      >
                      <b-form-input
                        v-model="item.name"
                      ></b-form-input>
                    </b-form-group>
                  </b-col>
                  <b-col cols="8">
                    <b-form-group
                      label="Template content"
                      description="First line is the subject. Use ${fieldname} to insert aggregated field names and ${events_as_csv} for a CSV attachment."
                      >
                      <b-form-textarea
                        v-model="item.body"
                        rows="10"
                      ></b-form-textarea>
                    </b-form-group>
                  </b-col>
                  <b-col cols="1">
                    <b-button
                      variant="danger"
                      size="sm"
                      @click.prevent="deleteTemplateInput(index)"
                      v-if="index != 0"
                      >X
                    </b-button>
                  </b-col>
                </b-row>
                <b-row>
                  <b-button
                    block
                    @click="increaseTemplateCounter"
                    variant="primary"
                  >+</b-button>
                </b-row>
              </b-container>
            </b-card-body>
          </b-collapse>
        </b-card>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex';
import parse from 'papaparse';
export default ({
  name: 'WebinputCSV',
  data: () => {
    return {
      username: "",
      password: "",
      showLogin: false,
      showAuthConfirm: false,
      wrongCredentials: false,
      overlay: false,
      inProgress: false,
      csvFile: null,
      csvText: "",
      csvPreviewText: "",
      delimiter: ",",
      delimiterOptions: [
        {value: ";", text: ";"},
        {value: ",", text: ","},
        {value: "#", text: "#"}
      ],
      quoteChar: '"',
      escapeChar: "\\",
      hasHeader: false,
      initialWhitespace: false,
      skipLines: 0,
      parserResult: {},
      lines: 0,
      errors: 0,
      timezones: [],
      timezone: '+00:00',
      dryrun: true,
      classificationType: "test",
      identifier: "test",
      code: "oneshot",
      tableHeader: [],
      tableData: [],
      currentPage: 1,
      pageOptions: [5, 10, 25, 100],
      perPage: 25,
      totalRows: 1,
      transferred: "",
      transferStatus: "text-danger",
      loginErrorText: "Wrong username or password",
      dataErrors: [],
      authConfirmErrorText: '',
      template: '',
      templates: [{'name': '', 'body': ''}],
      showMailgenLog: false,
      mailgenLog: '',
      mailgenStatus: '',
      mailgenInProgress: false,
      mailgenResult: '',
      mailgenVerbose: false,
      mailgenDryRun: false,
      mailgenPreview: '',
      showMailgenPreview: false,
      showMailgenPreviewRaw: false,
      mailgenPreviewParsed: {},
      validateWithBots: false,
      showRowModal: false,
      rowModalData: {},
      rowModalInProgress: false,
      errorMessage: null,
      showErrorModal: false,
      mailgenTargetGroups: [],
      mailgenTargetGroupsStatus: null,
    }
  },
  computed: {
    ...mapState(['user', 'loggedIn', 'hasAuth', 'classificationTypes', 'harmonizationFields', 'customFieldsMapping', 'requiredFields', 'mailgenAvailable', 'botsAvailable', 'mailgenAvailableTargetGroups', 'mailgenAvailableTargetGroupsStatus']),
  },
  mounted() {
    // Create timezone strings
    for (var i = -12; i <= 12; i++) {
      var timeZoneString = '';
      if (i < 0) {
          if ((i / -10) < 1) {
              timeZoneString = '-0' + (-i);
              this.timezones.push(timeZoneString);
          } else {
              this.timezones.push(i.toString());
          }
      } else {
          if ((i / 10) < 1) {
              timeZoneString = '+0' + i;
              this.timezones.push(timeZoneString);
          } else {
              this.timezones.push('+' + i.toString());
          }
      }
    }
    for (var j = 0; j < this.timezones.length; j++) {
        this.timezones[j] = this.timezones[j] + ':00';
    }
  },
  methods: {
    /**
     * Prepare and aggregate data and send the post request.
     */
    sendData: function(submit=true) {
      this.inProgress = true;
      this.transferred = "in progress..."
      let data = []
      for (let item of this.parserResult.data) {
        let sendItem = {};
        for (let ndx in this.tableHeader) {
          // check for header in csv. data is array or object
          // skip first column
          if (this.tableHeader[ndx].field !== "" && ndx !== 0) {
            let value;
            if (this.hasHeader) {
              value = item[this.tableHeader[ndx].key]
            } else {
              value = item[ndx-1];
            }
            sendItem[this.tableHeader[ndx].field] = this.prepare(this.tableHeader[ndx].field, value)
          }
        }
        data.push(sendItem);
      }
      let custom = this.computeCustom();
      let send = {
        timezone: this.timezone,
        data: data,
        custom: custom,
        dryrun: this.dryrun,
        submit: submit,
        username: this.username,
        password: this.password,
        validate_with_bots: this.validateWithBots,
      }
      var me = this;
      this.$http.post('api/upload', send)
        .then(response => {
          // authentication was successful, auth errors are treated below (401)
          me.authConfirmSubmit = false;
          me.authConfirmErrorText = null;
          me.$bvModal.hide("authconfirm-popup");
          if (response.status !== 200) {
            me.transferStatus = "text-danger";
            me.transferred = "Send failed!";
            me.inProgress = false;
            return;
          }
          response.json().then(data => {
            if (data.log && data.status == 'error') {
              this.errorMessage = data.log;
              this.showErrorModal = true;
              me.inProgress = false;
            }

            const num_errors = Object.keys(data.errors).length;
            me.transferred = (submit ? "Submitted " : "Validated ") + (data.total) + " lines. This resulted in " + num_errors + " validation errors and in total " + data.lines_invalid + " lines were invalid" + (submit ? ", these were not submitted" : "") + ". Therefore, " + (data.total - data.lines_invalid) + " lines were valid.";
            me.dataErrors = data.errors;
            if (num_errors) {
              me.transferStatus = "text-danger";
            } else {
              me.transferStatus = "text-black";
            }
            me.inProgress = false;
          })
        }, (response) => { // error
            if (response.status == 401) {
              // authentication error
              me.authConfirmErrorText = response.body;
            } else {
              // other error
              me.transferStatus = "text-danger";
              me.transferred = response.body;
              // auth was successful nevertheless, close the login and clear errors
              me.authConfirmSubmit = false;
              me.authConfirmErrorText = null;
              me.$bvModal.hide("authconfirm-popup");
            }
            me.inProgress = false;
            return;
        });
    },
    /**
     * Function to preprocess values.
     */
    prepare: function(field, value) {
      if (field === "extra") {
        try {
          value = JSON.parse(value)
        }
        catch(e) {
          return {data: value};
        }
        if (Array.isArray(value)) {
          return {data: value};
        }
      }
      return value;
    },
    reset: function() {
      this.csvFile = null;
      this.csvText = "";
    },
    /**
     * Update the table header and refresh view.
     */
    update: function(field, fieldname) {
      if (fieldname == null) {
        fieldname = "";
      }
      field.label = fieldname;
      field.field = fieldname;
      let ndx = this.tableHeader.findIndex(item => {
        if (item.key === field.key) {
          return true;
        }
      })
      this.tableHeader[ndx] = field;
      this.$refs.table.refresh();
    },
    /**
     * Trigger login.
     */
    signIn: function () {
      this.$store.dispatch("login", {
        username: this.username,
        password: this.password
      }).then(() => {
        this.wrongCredentials = false
        this.$bvModal.hide("login-popup")
        this.$store.dispatch("fetchClassificationTypes");
        this.$store.dispatch("fetchHarmonizationFields");
        this.$store.dispatch("fetchRequiredFields");
        this.$store.dispatch("fetchCustomFields");
        this.$store.dispatch("fetchMailgenAvailable");
        this.$store.dispatch("fetchBotsAvailable");
        this.$store.dispatch("fetchMailgenAvailableTargetGroups");
      }, (response) => {
        if (response.status !== 200) {
          this.loginErrorText = "Server not reachable.";
        }
        else {
          this.loginErrorText = "Wrong username or password.";
        }
        this.wrongCredentials = true
      })
    },
    /**
     * Trigger logout.
     */
    signOut: function () {
      this.username = "";
      this.password = "";
      this.wrongCredentials = false;
      this.csvText = "";
      this.csvFile = null;
      this.csvPreviewText = "",
      this.tableData = []
      this.tableHeader = []
      this.overlay = false;
      this.inProgress = false;
      this.transferred = "";
      this.delimiter = ",";
      this.quoteChar = '"';
      this.escapeChar = "\\";
      this.hasHeader = false;
      this.initialWhitespace = false;
      this.skipLines = 0;
      this.parserResult = {};
      this.timezone = '+00:00';
      this.dryrun = true;
      this.classificationType = "blacklist";
      this.identifier = "test";
      this.code = "oneshot";
      this.currentPage = 1;
      this.perPage = 25;
      this.$store.dispatch("logout")
    },
    /**
     * Read the uploaded csv file and trigger parsing the content.
     */
    readFromFile() {
      this.overlay = true;
      if (!this.csvFile) {
        this.csvText = "";
        this.parseCSV();
      }
      const me = this;
      return new Promise((resolve) => {
        if (this.csvFile) {
          var reader = new FileReader();
          reader.onload = function(event) {
            me.csvText = event.target.result;
            me.csvPreviewText = event.target.result.substring(0, 2000) + "\n\u2026";
            me.parseCSV();
            resolve();
          };
          reader.readAsText(this.csvFile);
        }
      });
    },
    showOverlay() {
      this.overlay = true;
    },
    /**
     * Parse the csv data and apply user options.
     */
    parseCSV() {
      if (this.csvText === "") {
        this.overlay = false;
      }
      // Option to trim whitespaces.
      if (this.initialWhitespace) {
        var regEx = "\\s*" + this.delimiter + "\\s*";
        var re = new RegExp(regEx,"g");
        this.csvText = this.csvText.replace(re, this.delimiter);
      }
      let count = 0;
      const me = this;
      this.parserResult.data = [];
      this.parserResult.errors = [];
      parse.parse(this.csvText, {
        delimiter: this.delimiter,
        quoteChar: this.quoteChar,
        escapeChar: this.escapeChar,
        header: this.hasHeader,
        skipEmptyLines: true,
        step: function(row) {
          if (me.skipLines > 0 && count < me.skipLines) {
            count++
            return;
          }
          me.parserResult.data.push(row.data);
          me.parserResult.errors.concat(row.errors);
          me.parserResult.meta = row.meta;
          return;
        }
      });
      if (this.parserResult.meta.aborted) {
        return;
      }
      if (this.parserResult.data.length === 0) {
        return;
      }
      this.lines = this.parserResult.data.length;
      this.errors = this.parserResult.errors.length;
      let columns;
      if (this.hasHeader
        && this.parserResult.meta.fields
      ) {
        columns = this.parserResult.meta.fields.map(function(i) {
          return {
            key: i,
            label: i
          }
        });
      } else  {
        columns = Array.apply(null, { length: this.parserResult.data[0].length }).map(function(i, ndx) {
          return {
            key: ""+ndx,
            label: ""
          }
        });
      }
      this.tableHeader.length = 0;
      this.tableHeader.push('Actions')
      for (let i in columns) {
        this.tableHeader.push({
          key: columns[i].key,
          label: columns[i].label,
          field: ""
        })

      }
      this.tableData = this.parserResult.data;
      this.overlay = false;
    },
    getTableCellClass(row) {
      if (this.dataErrors[row.index]) {
        return "table-danger"; // add a danger class to the row
      }
      return ""; // return an empty string for other rows
    },
    getTooltip(rowIndex, columnIndex) {
      console.log("getTooltip called with rowIndex", rowIndex, "columnIndex", columnIndex, "errors", this.dataErrors[rowIndex])
      if (this.dataErrors[rowIndex]) {
        return this.dataErrors[rowIndex].join('. ');
      }
      return "";
    },
    /**
     * when the user submits data, decide if login form is shown
     * if dryrun is active, just submit
     * ottherwise show the login form again
     */
    onSendData() {
      if (this.dryrun) {
        this.sendData();
      } else {
        // clear any previous error text
        this.authConfirmErrorText = null;
        this.showAuthConfirm = true;
      }
    },
    /**
     * Trigger a mailgen run
     */
    runMailgen() {
      //var me = this;
      this.mailgenInProgress = true;
      this.mailgenLog = '';
      this.$http.post('api/mailgen/run', {template: this.template, verbose: this.mailgenVerbose, dry_run: this.mailgenDryRun})
        .then(response => {
          this.mailgenInProgress = false;
          response.json().then(data => {
            this.mailgenStatus = "text-black";
            this.mailgenResult = data.result;
            this.mailgenLog = data.log;
          }).catch(err => {
            // body was not JSON
            this.mailgenStatus = "text-danger";
            this.mailgenResult = err;
        });
        }, (response) => { // error
          this.mailgenStatus = "text-danger";
          this.mailgenLog = response.body;
          this.mailgenInProgress = false;
          return;
        });
    },
    /**
     * very basic MIME parser
     * @param {str} mime: The email as string
     */
    parseMIME(mime) {
      const splitted = mime.split('\n');
      let isHeader = true;
      let isMimeHeader = false;
      let isBody = false;
      let line;
      let subject;
      let body = '';

        for(var lineindex = 0; lineindex < splitted.length; lineindex++) {
          line = splitted[lineindex];
          console.log('line:', line)
          if (isHeader) {
            console.log('is header')
            if (line.slice(0, 2) == '--') {
              line = '';
              isMimeHeader = true;
              isHeader = false;
            } else if (line.slice(0, 9) == 'Subject: ') {
              console.log('is subject')
              subject = line.slice(9);
            }
          } else if (isMimeHeader) {
            if (line == '\r') {
              isMimeHeader = false;
              isBody = true;
            }
          } else if (isBody) {
            if (line.slice(0, 2) == '--') {
              isBody = false;
            } else {
              body += line + '\n';
            }
          }
        }
      return [subject, body]
    },
    /**
     * Show an email preview
     */
    previewMailgen() {
      //var me = this;
      this.mailgenInProgress = true;
      this.mailgenLog = '';
      this.$http.post('api/mailgen/preview', {template: this.template, verbose: this.mailgenVerbose, dry_run: this.mailgenDryRun})
        .then(response => {
          this.mailgenInProgress = false;
          response.json().then(data => {
            this.mailgenStatus = "text-black";
            this.mailgenPreview = data.result;
            // clear the field, not used in case of success
            this.mailgenResult = '';
            this.mailgenLog = data.log;

            let [subject, body] = this.parseMIME(this.mailgenPreview)
            this.mailgenPreviewParsed = {subject: subject, body: body}
            this.showMailgenPreview = true;
          }).catch(err => {
            // body was not JSON
            this.mailgenStatus = "text-danger";
            this.mailgenResult = err;
        });
        }, (response) => { // error
          this.mailgenStatus = "text-danger";
          this.mailgenLog = response.body;
          this.mailgenInProgress = false;
          return;
        });
    },
    triggerShowRowModal (row) {
      this.rowModalInProgress = true;
      let data = []
      let item = this.parserResult.data[row.index];
      let sendItem = {};
      for (let ndx in this.tableHeader) {
        // check for header in csv. data is array or object
        // skip first column
        if (this.tableHeader[ndx].field !== "" && ndx !== 0) {
          let value;
          if (this.hasHeader) {
            value = item[this.tableHeader[ndx].key]
          } else {
            value = item[ndx-1];
          }
          sendItem[this.tableHeader[ndx].field] = this.prepare(this.tableHeader[ndx].field, value)
        }
      }
      data.push(sendItem);
      this.$http.post('api/bots/process', {
        data: data,
        custom: this.computeCustom(),
        dryrun: this.dryrun,
        template: this.template,
      })
        .then(response => {
          response.json().then(data => {
            this.rowModalData = data;

            if (data.notifications) {
              let [subject, body] = this.parseMIME(data.notifications[0])
              this.rowModalData.notifications = 'Subject: ' + subject + '\n\n' + body;
            }

            this.showRowModal = true;
            this.rowModalInProgress = false;
          }).catch(err => {
            // body was not JSON
            this.errorMessage = err;
            this.showErrorModal = true;
            this.rowModalInProgress = false;
        });
        }, (response) => { // error
          this.errorMessage = response.body;
          this.showErrorModal = true;
          this.rowModalInProgress = false;
          //this.rowModalLog = response.body;
          return;
        });
    },
    computeCustom() {
      let custom = {
          "custom_classification.type": this.classificationType,
      };
      // if target groups are available for selection, add the data (even if none selected, then it's an empty list). Otherwise, do not add the data.
      if (this.mailgenAvailableTargetGroupsStatus === true && this.mailgenAvailableTargetGroups.tag_values && this.mailgenAvailableTargetGroups.tag_values.length) {
        custom["custom_extra.target_groups"] = this.mailgenTargetGroups.map(value => this.mailgenAvailableTargetGroups.tag_name + ":" + value)
      }
      for (let field of this.customFieldsMapping) {
        custom["custom_"+field.key] = field.value;
      }
      return custom;
    },
    /**
     * Increate the number of template inputs
     */
    increaseTemplateCounter() {
      this.templates.push({'name': '', 'body': ''});
    },
    /**
     * Delete a template from the template array
     */
    deleteTemplateInput(index) {
      this.templates.splice(index, 1);
    }
  }
})
</script>
