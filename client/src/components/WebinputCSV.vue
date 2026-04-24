<template>
  <div>
    <b-navbar toggleable="lg" type="dark" variant="info">
      <b-navbar-brand href="#">IntelMQ - Webinput CSV</b-navbar-brand>
      <b-navbar-nav>
        <b-nav-text>
          <small>
            Client Version: {{ clientVersion }}
          </small>
        </b-nav-text>
        <b-nav-text v-if="backendVersion" style="margin-left: 0.5em">
          <small>
            Backend Version: {{ backendVersion }}
          </small>
        </b-nav-text>
        <b-nav-item href="https://intevation.github.io/intelmq-webinput-csv/" target="_blank">
          <small style="text-decoration: underline;">
            Documentation ↗
          </small>
        </b-nav-item>
      </b-navbar-nav>
      <b-navbar-nav v-if="hasAuth" class="ml-auto">
        <b-button v-if="!loggedIn" v-b-modal.login-popup size="sm" class="my-2 my-sm-0">Login</b-button>
        <b-button v-if="loggedIn" size="sm" class="my-2 my-sm-0" @click="signOut">Logout</b-button>
      </b-navbar-nav>
    </b-navbar>
    <div>
      <b-modal v-model="showLogin" id="login-popup" title="IntelMQ - Webinput-CSV - Sign in">
        <label v-if="wrongCredentials" class="text-danger">{{ loginErrorText }}</label>
        <b-form>
          <div>
            <label for="username">Username</label>
            <b-form-input v-model="username" type="text" id="username" placeholder="Name" @keyup.enter="signIn"/>
            <label for="password">Password</label>
            <b-form-input v-model="password" type="password" id="password" placeholder="Password" @keyup.enter="signIn"/>
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
      <b-modal v-model="showAuthConfirm" id="authconfirm-popup" title="Confirm Authentication for Submission" @hide="usernameConfirm = '', passwordConfirm = ''">
        <b-form>
          <div>
            <label for="usernameConfirm">Username</label>
            <b-form-input v-model="usernameConfirm" type="text" id="usernameConfirm" placeholder="Name"/>
            <label for="passwordConfirm">Password</label>
            <b-form-input v-model="passwordConfirm" type="password" id="passwordConfirm" placeholder="Password"/>
          </div>
        </b-form>
        <template #modal-footer>
            <b-button
              variant="primary"
              size="sm"
              class="float-right"
              @click="sendDataConfirmed"
            >
              Submit
            </b-button>
        </template>
      </b-modal>
      <b-modal v-model="showMailgenLog" scrollable centered size="xl" id="mailgenLog-popup" title="Mailgen Log">
        <pre><code class="text-black">{{ mailgenLog }}</code></pre>
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
      <b-modal v-model="showMailgenPreview" scrollable centered size="xl" id="mailgenPreview-popup" title="Mailgen Template Preview">
        <small>Please note that this preview uses example data and thus does not take the CERT-Bund rules into account. The example data contains more data and aggregated fields than real data. To consider the input data, use the tools in the "Data Validation and Submission" section.</small>
        <h5 title="Subject" style="margin-top: 10px;">Subject: {{mailgenPreviewParsed.subject}}</h5>
        <h6 title="To">To: {{mailgenPreviewParsed.to}}</h6>
        <h6 title="Content-Type">Content Type: {{ mailgenPreviewParsed.contentType }}</h6>
        <pre><code class="text-black">{{ mailgenPreviewParsed.body }}</code></pre>
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
        <pre><code class="text-black">{{ mailgenPreview }}</code></pre>
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
        <pre><code>{{ errorMessage }}</code></pre>
      </b-modal>
      <b-modal v-model="templateDeletionModal" scrollable centered size="xl" id="templateDeletetion-popup" title="Are you sure?"
        @ok="dropTemplate"
        >
        Are you sure? This will delete the template file <strong><code>{{ templateToDelete.template_name }}</code></strong> from the server. It cannot be recovered unless you have a backup of it.
      </b-modal>
    </div>
    <div v-show="loggedIn">
      <b-overlay :show="parsingInProgress || uploadInProgress" opacity="0.5">
        <div class="accordion" role="tablist">
          <b-card no-body class="mb-1">
            <b-card-header header-tag="header" class="p-1" role="tab">
              <b-button block @click="accordionState = 1" variant="info">CSV Content</b-button>
            </b-card-header>
            <b-collapse :visible="accordionState === 1" accordion="main-accordion" role="tabpanel">
              <b-card-body>
                <b-container fluid>
                  <b-row>
                    <b-col cols="11">
                      <b-form-group>
                        <b-form-file
                          v-model="csvFile"
                          :disabled="parsingInProgress"
                          placeholder="Choose a file or drop it here…"
                          drop-placeholder="Drop file here…"
                          @input="csvSource = $event ? 2 : 1, csvText = '', needsReparse = true"
                        />
                      </b-form-group>
                    </b-col>
                    <b-col>
                      <b-button @click="csvSource = 1, csvText = '', csvFile = null, needsReparse = true, csvSource = 1">Clear</b-button>
                    </b-col>
                  </b-row>
                </b-container>
                <b-container fluid>
                  <b-form-group
                    v-show="csvSource === 1"
                    label="Or paste CSV data here"
                    label-for="csv-textarea"
                  >
                    <b-form-textarea
                      id="csv-textarea"
                      v-model="csvText"
                      :disabled="parsingInProgress"
                      placeholder="CSV data"
                      rows="5"
                      @input="csvSource = 1, csvFile = null, needsReparse = true"
                    />
                  </b-form-group>
                  <b-form-group
                    v-show="csvSource === 2"
                    :label="'Preview of ' + csvFileName"
                    label-for="csv-preview-textarea"
                  >
                    <b-form-textarea
                      id="csv-preview-textarea"
                      v-model="csvFilePreview"
                      rows="5"
                      readonly
                    />
                  </b-form-group>
                </b-container>
                <b-modal
                  ref="parseErrorModal"
                  ok-only
                  centered
                >
                  <div>
                    <div v-if="parseError instanceof Array">
                      <p>Got error(s) inside the CSV data:</p>
                      <ul>
                        <li v-for="(el, i) in parseError" :key="i">{{ el }}</li>
                      </ul>
                    </div>
                    <div v-else>
                      <p>Could not parse the CSV data: {{ parseError }}</p>
                    </div>
                  </div>
                </b-modal>
                <b-container fluid>
                  <b-row>
                    <b-col>
                      <b-form-group label-cols=7 label="Delimiter">
                        <b-form-select
                          v-model="delimiter"
                          :options="[{value: ';', text: ';'}, {value: ',', text: ','}, {value: '#', text: '#'}]"
                          @input="needsReparse = true"
                        />
                      </b-form-group>
                    </b-col>
                    <b-col>
                      <b-form-group label-cols=7 label="Quote character">
                        <b-form-input
                          v-model="quoteChar"
                          type="text"
                          placeholder='"'
                          @input="needsReparse = true"
                        />
                      </b-form-group>
                    </b-col>
                    <b-col>
                      <b-form-group label-cols=7 label="Escape character">
                        <b-form-input
                          v-model="escapeChar"
                          type="text"
                          placeholder="\"
                          @input="needsReparse = true"
                        />
                      </b-form-group>
                    </b-col>
                    <b-col>
                      <b-form-group label-cols=7 label="Has Header">
                        <b-form-checkbox
                          v-model="hasHeader"
                          @input="needsReparse = true"
                        />
                      </b-form-group>
                      <small tabindex="-1" class="form-text text-muted">CSV data must not contain duplicate headers</small>
                    </b-col>
                    <b-col>
                      <b-form-group id="option1" label-cols=9 label="Skip initial Whitespace">
                        <b-form-checkbox
                          v-model="initialWhitespace"
                          @input="needsReparse = true"
                        />
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
                          @input="needsReparse = true"
                        />
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

          <b-card no-body class="mb-1" style="overflow-x: visible;">
            <b-card-header header-tag="header" class="p-1" role="tab">
              <b-button :disabled="!newCsvData" block @click="navigateToValidationAndSubmission" variant="info">Data Validation and Submission</b-button>
            </b-card-header>
            <b-collapse :visible="accordionState === 2" accordion="main-accordion" role="tabpanel">
              <b-card-body>
                <b-container fluid>
                  <b-row>
                    <b-col>
                      <label>CSV Parsing Result: {{ parsedData.length }} lines</label>
                      <b-form-group label-cols=4 label="Timezone">
                        <b-form-select
                          v-model="timezone"
                          :options="timezones"
                        />
                      </b-form-group>
                      <b-form-group label-cols=4 label="Dryrun">
                        <b-form-checkbox
                          ref="dryrunCheckbox"
                          v-model="dryrun"
                          switch
                        />
                        <b-tooltip
                          v-if="$refs.dryrunCheckbox" :target="$refs.dryrunCheckbox" triggers="manual" :show="showDryrunCheckboxTooltip"
                          title="Override the values of classification.type and (if set as fallback value) classification.identifier with 'test'."
                        />
                      </b-form-group>
                      <b-form-group label-cols=4 label="Use custom workflow">
                        <b-form-checkbox
                          ref="customWorkflowCheckbox"
                          v-model="customWorkflow"
                          switch
                          :disabled="!botsAvailable.status"
                        />
                        <b-tooltip
                          v-if="$refs.customWorkflowCheckbox" :target="$refs.customWorkflowCheckbox" triggers="manual" :show="showCustomWorkflowCheckboxTooltip"
                          :title="'Off: Submit data to standard IntelMQ workflow using existing templates for notifications.\nOn: Submit data to custom workflow.' + (!botsAvailable.status ? botsAvailable.reason : '')"
                        />
                      </b-form-group>
                      <b-form-group
                        :label="mailgenAvailableTargetGroups.tag_name || 'Target groups'"
                        label-cols=4
                        v-if="mailgenAvailable">
                        <b-row
                          v-if="mailgenAvailableTargetGroupsStatus === true && mailgenAvailableTargetGroups.tag_values && mailgenAvailableTargetGroups.tag_values.length">
                          <b-col cols="9">
                            <b-form-checkbox-group
                              v-model="mailgenTargetGroups"
                              :options="mailgenAvailableTargetGroups.tag_values"
                              v-if="mailgenAvailableTargetGroupsStatus === true && mailgenAvailableTargetGroups.tag_values && mailgenAvailableTargetGroups.tag_values.length"
                            />
                          </b-col>
                          <b-col>
                            <b-row>
                              <b-col style="margin-bottom: 2px;">
                                <b-button @click="onTargetGroupsSelectAll" size="sm">
                                Select all
                                </b-button>
                              </b-col>
                              <b-col>
                                <b-button @click="onTargetGroupsSelectNone" size="sm">
                                Select none
                                </b-button>
                              </b-col>
                            </b-row>
                          </b-col>
                        </b-row>
                        <span
                          v-if="mailgenAvailableTargetGroupsStatus === true && mailgenAvailableTargetGroups.tag_values && mailgenAvailableTargetGroups.tag_values.length == 0"
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
                            <b-button @click="sendDataNoSubmit" :disabled="uploadInProgress" variant="info">Validate data</b-button>
                          </b-col>
                          <b-col>
                            <b-button
                              @click="sendDataMaybeConfirm"
                              :disabled="uploadInProgress || (allowValidationOverride == false && !parsedDataValid)"
                              variant="primary"
                              v-b-tooltip.hover
                              :title="allowValidationOverride == false ? (parsedDataValid === null ? 'Data validation required' : dataVaild ? '' : 'Data validation failed') : ''"
                              >Submit to {{ customWorkflow ? 'custom workflow' : 'standard workflow' }}</b-button>
                          </b-col>
                          <b-col>
                            <label style="margin-left: 10px;" v-show="uploadInProgress">In progress…</label>
                            <label style="margin-left: 10px;" v-show="!uploadInProgress && uploadStatusMessage" :class="uploadSuccessful ? 'text-black' : 'text-danger'">{{ uploadStatusMessage }}</label>
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
                      <h4>Fallback values</h4>
                      <b-form-group label-cols=4 label="classification.type">
                        <b-form-select
                          v-model="classificationType"
                          :options="classificationTypes"
                          :disabled="dryrun"
                        />
                      </b-form-group>
                      <b-form-group v-for="field in customFieldsMapping" :key="field.key" :id="field.key" label-cols=4 :label="field.key">
                        <b-form-input
                          v-model="field.value"
                          type="text"
                          :disabled="field.key == 'classification.identifier' && dryrun"
                          />
                      </b-form-group>
                    </b-col>
                  </b-row>
                </b-container>
                <harmonization-fields-table
                  :fieldAssignments="fieldAssignments"
                  :fieldOptions="harmonizationFields"
                  :dataRows="parsedData"
                  :dataCandidateTypes="dataCandidateTypes"
                  :dataErrors="dataErrors"
                  :errorFieldAssignments="errorFieldAssignments"
                  :getRowPromise="getRowPromise"
                  :getFieldNameValidationPromise="getFieldNameValidationPromise"
                  @updateField="onUpdateField"
                />
              </b-card-body>
            </b-collapse>
          </b-card>

          <b-card no-body class="mb-1" style="overflow-x: visible;">
            <b-card-header header-tag="header" class="p-1" role="tab">
              <b-button
                :disabled="!mailgenAvailable || needsReparse"
                block
                @click="accordionState = 3"
                variant="info"
                :title="!mailgenAvailable ? 'Mailgen is not installed/available' : needsReparse ? 'Click on &quot;Data Validation and Submission&quot; first to parse the data' : 'Set Mailgen Templates and Start a Mailgen Run'"
              >Send Notifications</b-button>
            </b-card-header>
            <b-collapse :visible="accordionState === 3" accordion="main-accordion" role="tabpanel" @show="onShowNotificationAccordion">
              <b-card-body>
                <b-container fluid>
                  <b-row align-v="center">
                    <b-col>
                      <b-form-group
                        label-cols="auto"
                        label="Verbose Logs"
                        v-b-tooltip.hover
                        title="Activate verbose logging in Mailgen for more details on processing"
                      >
                        <b-form-checkbox
                          v-model="mailgenVerbose"
                          switch
                        />
                      </b-form-group>
                      <b-form-group
                        label-cols="auto"
                        label="Simulate"
                        v-b-tooltip.hover
                        title="Only simulate Mailgen run, do not actually send notifications"
                      >
                        <b-form-checkbox
                          v-model="mailgenDryRun"
                          switch
                        />
                      </b-form-group>
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
                          <b-button
                            v-b-tooltip.hover
                            @click="previewMailgenTemplate(showDialog=true)"
                            variant="primary"
                            :disabled="!mailgenAvailable || !mailgenTemplate"
                            title="Template Preview"
                            block
                            >Show Template {{ (mailgenTemplateValidationStatus == 'text-danger') ? 'Log' : 'Preview' }}</b-button>
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
                        <label style="margin-left: 10px;" :class="mailgenStatus">{{ mailgenResult }}</label><br />
                        <b-button @click="showMailgenLog=true" v-b-modal.mailgenLog-popup v-if="mailgenLog && mailgenLog != mailgenResult">Show complete log</b-button>
                      </b-overlay>
                    </b-col>
                  </b-row>
                  <b-row v-if="!mailgenMultiTemplatesEnabled">
                    <b-col>
                      <h4>Template</h4>
                    </b-col>
                  </b-row>
                  <b-row v-if="!mailgenMultiTemplatesEnabled">
                    <b-col cols="3" style="text-align: left;">
                      <p>
                        The template given here is fixed for all notifications sent by this Mailgen run.
                        The Template is not saved to disk.
                      </p>
                      <p>First line is the subject. Use <code>${fieldname}</code> to insert aggregated field names and <code>${events_as_csv}</code> for a CSV attachment.</p>
                      <p>If the Template is empty, Mailgen uses its default templates.</p>
                      <p>Mailgen started by other means (command line or automated jobs), uses the templates present on disk.</p>
                    </b-col>
                    <b-col>
                      <b-row>
                        <b-col>
                          <span
                            :class="mailgenTemplateValidationStatus"
                            >{{mailgenTemplateValidationText}}
                        </span>
                        </b-col>
                        <b-col>
                          <b-form-group
                            label="Replace text with existing template from disk:"
                            label-cols="auto">
                            <v-select
                              :options="mailgenTemplateNames"
                              v-model="mailgenTemplatePrototype"
                              @input="onMailgenTemplatePrototypeSelected"
                              width="100%"
                            />
                        </b-form-group>
                        </b-col>
                      </b-row>
                      <b-row>
                        <b-col>
                          <b-form-group width="100%">
                            <b-form-textarea
                              id="template"
                              v-model="mailgenTemplate"
                              rows="10"
                              width="100%"
                              @input="validateMailgenTemplateContentDebounce"
                            />
                          </b-form-group>
                        </b-col>
                      </b-row>
                    </b-col>
                  </b-row>
                  <h4 v-if="mailgenMultiTemplatesEnabled">Templates:</h4>
                  <b-row align-h="center" style="margin-buttom: 30px" v-if="mailgenMultiTemplatesEnabled">
                    <span style="max-width: 700px">
                      Mailgen started via this interface (only) uses the templates shown here. It does not matter if the templates are saved to the file on the server.
                      Templates not saved to disk are not retained and are only available in this session.
                      Mailgen started by other means (command line or automated jobs), uses the templates present on disk.
                    </span>
                  </b-row>
                  <b-container v-if="mailgenMultiTemplatesEnabled">
                    <b-row v-for="(item, index) in mailgenTemplates" v-bind:key="index" class="item">
                      <b-col>
                        <b-row>
                          <b-form-group
                            label="Template name"
                            description="With an empty name, the template will be ignored"
                            >
                            <b-form-input
                              v-model="item.name"
                              @input="validateTemplateNameDebounced(index); validateTemplateContent(index)"
                              :state="item.state"
                            />
                            <b-form-invalid-feedback :id="'template-name-feedback-' + index">
                              Duplicate Template Name
                            </b-form-invalid-feedback>
                          </b-form-group>
                        </b-row>
                        <b-row>
                          <b-overlay
                            :show="mailgenInProgress"
                            rounded
                            opacity="0.5"
                            spinner-small
                            spinner-variant="primary"
                            class="d-inline-block"
                          >
                            <b-button
                              v-b-tooltip.hover
                              @click="previewMailgen(index, showDialog=true)"
                              variant="primary"
                              :disabled="!mailgenAvailable || !item.body"
                              title="Preview this template"
                              block
                              >Show Template {{ (item.validationStatus == 'text-danger') ? 'Log' : 'Preview' }}</b-button>
                          </b-overlay>
                        </b-row>
                        <b-row>
                          <span
                            style="color: green"
                            v-if="mailgenTemplatesServer[index] && mailgenTemplatesServer[index].name == ''"
                            title="This template does not exist on the server"
                            >new</span>
                          <span
                            style="color: green"
                            v-if="mailgenTemplatesServer[index] && item.name.trim() != mailgenTemplatesServer[index].name.trim() && mailgenTemplatesServer[index].name != ''"
                            >modified
                              <b-button
                                variant="info"
                                size="sm"
                                @click.prevent="item.name = mailgenTemplatesServer[index].name"
                                title="Revert to the original state"
                                style="margin-top: 10px"
                                >↶
                              </b-button>
                            </span>
                          </b-row>
                          <b-row>
                            <span
                              :class="item.validationStatus"
                              >{{item.validationText}}
                            </span>
                          </b-row>
                        </b-col>
                        <b-col cols="8">
                          <b-form-group
                            label="Template content"
                            description="First line is the subject. Use ${fieldname} to insert aggregated field names and ${events_as_csv} for a CSV attachment."
                            >
                            <b-form-textarea
                              v-model="item.body"
                              rows="10"
                              @input="validateTemplateContent(index)"
                            />
                          </b-form-group>
                        </b-col>
                        <b-col cols="1">
                          <b-button
                            block
                            variant="info"
                            size="sm"
                            @click.prevent="deleteTemplateInput(index)"
                            title="Remove this template input field. Does not remove it from the server."
                            v-if="index != 0"
                            style="font-size: 1.5em"
                            >❌
                          </b-button>
                          <b-button
                            block
                            size="sm"
                            variant="danger"
                            :disabled="mailgenTemplatesServer[index] && item.name.trim() != mailgenTemplatesServer[index].name.trim()"
                            @click.prevent="showTemplateDeletionModal(index, item.name)"
                            title="Delete the template file from the server"
                            style="font-size: 1.5em"
                          >🗑️</b-button>
                          <b-button
                            block
                            size="sm"
                            variant="success"
                            :disabled="mailgenTemplatesServer[index] && item.name.trim() == mailgenTemplatesServer[index].name.trim() && item.body.trim() == mailgenTemplatesServer[index].body.trim()"
                            @click.prevent="saveTemplate(index, item.name, item.body)"
                            title="Save the template file on the server"
                            style="font-size: 1.5em"
                          >💾</b-button>
                          <span
                            style="color: green"
                            v-if="mailgenTemplatesServer[index] && item.body.trim() != mailgenTemplatesServer[index].body.trim() && mailgenTemplatesServer[index].name != ''"
                            >modified
                            <b-button
                              variant="info"
                              size="sm"
                              @click.prevent="item.body = mailgenTemplatesServer[index].body"
                              v-if="mailgenTemplatesServer[index] && item.body.trim() != mailgenTemplatesServer[index].body.trim()"
                              title="Revert to the original state"
                              style="margin-top: 10px"
                              >↶
                              </b-button>
                          </span>
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
                </b-container>
              </b-card-body>
            </b-collapse>
          </b-card>
        </div>
      </b-overlay>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex';
import parse from 'papaparse';
import { debounce } from 'lodash';
import harmonizationFieldsTable from './HarmonizationFieldsTable.vue';
import { parseMIME } from '../util/parseMIME.js';
import { ip_regex, timestamp_regex } from '../util/formats.js';

const prepare = (field, value) => {
  if (field === "extra") {
    try {
      value = JSON.parse(value)
    }
    catch (e) {
      return {data: value};
    }
    if (Array.isArray(value)) {
      return {data: value};
    }
  }
  return value;
};

const rowToSendable = (row, fieldsMap) => {
  var r = {};
  for (let [field, i] of fieldsMap) {
    r[field] = prepare(field, row[i]);
  }
  return r;
};

const sanitizeFieldName = field =>
  field ? field.trim().toLowerCase().replaceAll(/ /g, '_').replaceAll(/[^a-zA-Z0-9_.]+/g, '') : '';

const sanitizeFieldList = (fields, allFields) => {
  var r = Array(fields.length);
  for (let i = 0; i < fields.length; ++i) {
    let field = sanitizeFieldName(fields[i]);
    if (allFields.includes(field)) {
      r[i] = field;
      continue;
    }
    if (!field.startsWith('extra.')) field = 'extra.' + field;
    // Prevent duplicates
    r[i] = r.includes(field) ? '' : field;
  }
  return r;
};

const resetProperties = obj => {
  obj['username'] = '';
  obj['password'] = '';
  obj['usernameConfirm'] = '';
  obj['passwordConfirm'] = '';
  obj['accordionState'] = 1; // 0: none; 1: input CSV; 2: validation and submission; 3: send notifications
  obj['delimiter'] = ',';
  obj['quoteChar'] = '"';
  obj['escapeChar'] = '\\';
  obj['hasHeader'] = true;
  obj['initialWhitespace'] = false;
  obj['skipLines'] = 0;
  obj['csvText'] = '';
  obj['csvFile'] = null;
  obj['csvSource'] = 1; // 1: text input; 2: file input
  obj['parsingInProgress'] = false;
  obj['parsedDataInputCsv'] = null; // The CSV data that was used as input for the last parse
  obj['parsedData'] = []; // The result of the last parse
  obj['fieldAssignments'] = [];
  obj['needsReparse'] = true; // false iff parsedData is up-to-date with newCsvData
  obj['uploadData'] = null;
  obj['uploadInProgress'] = false;
  obj['parsedDataValid'] = null;
  obj['uploadStatusMessage'] = '';
  obj['uploadSuccessful'] = false;
  obj['timezone'] = '+00:00';
  obj['dryrun'] = true;
  obj['classificationType'] = 'test';
  obj['dataErrors'] = [];
  obj['errorFieldAssignments'] = [];
};

export default ({
  name: 'WebinputCSV',
  components: {harmonizationFieldsTable},
  data() {
    const o = {
      showLogin: false,
      showAuthConfirm: false,
      wrongCredentials: false,
      loginErrorText: '',
      csvFilePreview: 'No data available',
      parseError: null,
      timezones: [],
      showMailgenLog: false,
      mailgenLog: '',
      mailgenStatus: '',
      mailgenInProgress: false,
      mailgenResult: '',
      mailgenVerbose: false,
      mailgenDryRun: true,
      mailgenPreview: '',
      showMailgenPreview: false,
      showMailgenPreviewRaw: false,
      mailgenPreviewParsed: {},
      customWorkflow: false,
      errorMessage: null,
      showErrorModal: false,
      mailgenTargetGroups: [],
      clientVersion: "1.2.7",
      templateDeletionModal: false,
      templateToDelete: {'index': null, 'template_name': null},
      mailgenTemplate: '',
      mailgenTemplateValidationText: '',
      mailgenTemplateValidationStatus: null,
      mailgenTemplatePrototype: null,
      showDryrunCheckboxTooltip: false,
      showCustomWorkflowCheckboxTooltip: false
    };
    resetProperties(o);
    return o;
  },
  computed: {
    mailgenTemplateNames() {
      return this.mailgenTemplatesServer.map(template => template.name)
    },
    mailgenTemplateMap() {
      return Object.fromEntries(this.mailgenTemplatesServer.map((template) => [template.name, template.body]))
    },
    assignedColumns() {
      return this.fieldAssignments.filter(field => field);
    },
    newCsvData() {
      return this.csvSource === 1 ? this.csvText : this.csvFile;
    },
    csvFileName() {
      if (this.csvSource !== 2 || !this.csvFile) return '[error]';
      return this.csvFile.name;
    },
    fieldsMap() {
      var r = [];
      for (let i = 0; i < this.fieldAssignments.length; ++i) {
        const field = this.fieldAssignments[i];
        if (field) r.push([field, i]);
      }
      return r;
    },
    sendableDataFull() { // data in format to be sent to backend
      return this.parsedData.map(row => rowToSendable(row, this.fieldsMap));
    },
    sendableDataOneRow() {
      return this.parsedData.slice(0, 1).map(row => rowToSendable(row, this.fieldsMap));
    },
    dataCandidateTypes() {
      var a = this.parsedData.slice(0, 200); // Only consider the first 200 rows for performance
      if (a.length === 0) return [];
      var cols = a[0].length;
      var r = Array(cols);
      for (let i = 0; i < cols; ++i) {
        r[i] = {
          ip: a.every(row => ip_regex.test(row[i])),
          timestamp: a.every(row => timestamp_regex.test(row[i]))
        };
      }
      return r;
    },
    ...mapState(['user', 'loggedIn', 'hasAuth', 'classificationTypes', 'harmonizationFields', 'customFieldsMapping', 'requiredFields', 'mailgenAvailable', 'botsAvailable', 'mailgenAvailableTargetGroups', 'mailgenAvailableTargetGroupsStatus', 'backendVersion', 'mailgenTemplatesServer', 'mailgenTemplates', 'mailgenMultiTemplatesEnabled', 'mailgenTemplateDefaultTemplateName', 'customWorkflowDefault', 'allowValidationOverride']),
  },
  mounted() {
    this.$store.dispatch("fetchBackendVersion");
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
    // Show tooltip only if the mouse is over the switch rather than anywhere within its "table cell".
    // To accomplish this, we unfortunately need to rely on an implementation detail of b-form-checkbox: its label.
    // FIXME: Implement our own checkbox so we can avoid this?
    var dryrunCheckboxLabel = this.$refs.dryrunCheckbox.$el.querySelector('label');
    dryrunCheckboxLabel.addEventListener('mouseenter', () => {
      this.showDryrunCheckboxTooltip = true;
    });
    dryrunCheckboxLabel.addEventListener('mouseleave', () => {
      this.showDryrunCheckboxTooltip = false;
    });
    var customWorkflowCheckboxLabel = this.$refs.customWorkflowCheckbox.$el.querySelector('label');
    customWorkflowCheckboxLabel.addEventListener('mouseenter', () => {
      this.showCustomWorkflowCheckboxTooltip = true;
    });
    customWorkflowCheckboxLabel.addEventListener('mouseleave', () => {
      this.showCustomWorkflowCheckboxTooltip = false;
    });
  },
  watch: {
    customWorkflowDefault(newCustomWorkflowDefault) {
      this.customWorkflow = newCustomWorkflowDefault;
    },
    csvFile(newCsvFile) {
      if (!newCsvFile) {
        this.csvFilePreview = 'No data available';
        return;
      }
      this.csvFilePreview = 'Loading…';
      const truncated = newCsvFile.size > 10000;
      const blob = truncated ? newCsvFile.slice(0, 10000) : newCsvFile;
      blob.text().then(
        text => {
          if (this.csvFile !== newCsvFile) return; // file changed, our data is outdated
          this.csvFilePreview = truncated ? text + '…' : text;
        },
        reason => {
          if (this.csvFile !== newCsvFile) return;
          this.csvFilePreview = 'Error: ' + reason;
        }
      );
    }
  },
  methods: {
    navigateToValidationAndSubmission() {
      if (!this.needsReparse) {
        this.accordionState = 2;
        return;
      }
      const newCsvData = this.newCsvData;
      // This would need additional checks: a reparse is also required if e.g. the data is the same but hasHeader is different
      /*if (newCsvData && newCsvData === this.parsedDataInputCsv) {
        this.needsReparse = false;
        this.accordionState = 2;
        return;
      }*/
      // Reparse
      const hasHeader = Boolean(this.hasHeader);
      // skipLines: Skip the first n (nonempty) lines after the header.
      const skipRows = +this.skipLines;
      let fieldsCount = null;
      let inputRows = [];
      let error = null;
      let finished = false;
      const finish = () => {
        if (finished) return;
        finished = true;
        if (this.newCsvData !== newCsvData) {
          console.error('CSV data changed during parse');
          return;
        }
        if (error === null && inputRows.length === 0) {
          error = 'Got no rows in input';
        }
        if (error !== null) {
          this.accordionState = 1; // Should already be this value
          this.parseError = error;
          this.$refs.parseErrorModal.show();
        } else {
          if (hasHeader) {
            this.fieldAssignments = sanitizeFieldList(inputRows[0], this.harmonizationFields || []);
            this.parsedData = inputRows.slice(1);
          } else {
            this.fieldAssignments = Array(fieldsCount).fill('');
            this.parsedData = inputRows;
            const ipIndex = this.dataCandidateTypes.findIndex(el => el.ip);
            if (ipIndex >= 0) this.fieldAssignments[ipIndex] = 'source.ip';
            const timestampIndex = this.dataCandidateTypes.findIndex(el => el.timestamp);
            if (timestampIndex >= 0) this.fieldAssignments[timestampIndex] = 'time.source';
          }
          this.dataErrors = [];
          this.errorFieldAssignments = [];
          this.parsedDataValid = null;
          this.uploadStatusMessage = '';
          this.uploadSuccessful = false;
          this.needsReparse = false;
          this.accordionState = 2;
        }
        this.parsedDataInputCsv = newCsvData;
        this.parsingInProgress = false;
      };
      if (!newCsvData) {
        error = 'Got no input data';
        finish();
        return;
      }
      let rowNum = -hasHeader;
      this.parsingInProgress = true;
      parse.parse(newCsvData, {
        delimiter: this.delimiter,
        quoteChar: this.quoteChar,
        escapeChar: this.escapeChar,
        header: false, // We handle this ourselves (we want to get arrays, not keyed objects)
        skipEmptyLines: true,
        worker: true,
        step: (results, parser) => {
          if (results.errors.length > 0) {
            error = results.errors;
            parser.abort();
            finish();
            return;
          }
          const row = results.data;
          /*row._intelmqwebinputcsv_row =*/ rowNum++;
          // "rowNum !== 0": Don't skip if this is the header row
          if (rowNum !== 0 && rowNum <= skipRows) return;
          if (fieldsCount === null) fieldsCount = row.length;
          else if (row.length !== fieldsCount) {
            error = `Got row with different number of fields (expected ${fieldsCount}, got ${row.length})`;
            parser.abort();
            finish();
            return;
          }
          inputRows.push(row);
        },
        complete: finish,
        error: e => {
          error = `Got error while reading from file: ${e}`;
          finish();
        }
      });
    },
    onUpdateField(e) {
      let {column, value} = e;
      column = Number(column);
      if (!(0 <= column && column < this.fieldAssignments.length)) return;
      if (value) {
        value = sanitizeFieldName(value);
        if (!value) return;
      } else {
        value = '';
      }
      this.$set(this.fieldAssignments, column, value);
    },
    sendDataNoSubmit() {
      this.sendData({}, false);
    },
    sendDataMaybeConfirm() {
      if (this.dryrun) this.sendData({
        dryrun: true,
        // Dryruns still need authentification somehow (see serve.py)
        username: this.username,
        password: this.password
      });
      else this.showAuthConfirm = true;
    },
    sendDataConfirmed() {
      this.sendData({
        username: this.usernameConfirm,
        password: this.passwordConfirm
      });
      this.showAuthConfirm = false;
      this.usernameConfirm = '';
      this.passwordConfirm = '';
    },
    /**
     * Prepare and aggregate data and send the post request.
     */
    sendData(send, submit=true) {
      send['submit'] = submit;
      send['timezone'] = this.timezone;
      send['data'] = this.sendableDataFull;
      send['custom'] = this.computeCustom();
      send['validate_with_bots'] = this.customWorkflow;
      send['assigned_columns'] = this.assignedColumns;
      const customWorkflow = this.customWorkflow;
      const fieldAssignments = this.fieldAssignments;
      this.uploadData = send;
      this.uploadInProgress = true;
      this.$http.post('api/upload', send).then(response => {
        if (this.uploadData !== send) return;
        response.json().then(data => {
          if (this.uploadData !== send) return;
          this.uploadInProgress = false;
          if (data.status === 'error') {
            this.errorMessage = data.log;
            this.showErrorModal = true;
            this.uploadStatusMessage = 'Server error';
            this.uploadSuccessful = false;
            return;
          }
          const errors = data.errors || {};
          const numErrors = Object.keys(errors).length;
          const success = numErrors === 0;
          this.uploadStatusMessage = (submit ? `Submitted ${data.input_lines} lines to IntelMQ ${customWorkflow ? 'database' : 'processing queue'}.` : `Validated ${data.input_lines} lines.`) + ` Of these, ${data.input_lines - data.input_lines_invalid} were valid. This resulted in ${numErrors} validation errors and in total ${data.input_lines_invalid} lines were invalid${submit ? ', these were not submitted' : ''}.` + (customWorkflow ? ` After bot validation, the input data resulted in ${data.output_lines} events and ${data.output_lines_invalid} events occurred (invalid events).` : '');
          this.uploadSuccessful = success;
          if (!submit) this.parsedDataValid = success;
          this.dataErrors = errors;
          this.errorFieldAssignments = fieldAssignments;
        }, (/*error*/) => {
          if (this.uploadData !== send) return;
          this.uploadInProgress = false;
          this.uploadStatusMessage = 'Got invalid JSON in response';
          this.uploadSuccessful = false;
        });
      }, response => {
        if (this.uploadData !== send) return;
        this.uploadInProgress = false;
        this.uploadStatusMessage = `${response.status === 401 ? 'Authentication error' : 'Error'}: ${response.bodyText}`;
        console.log(response);
        this.uploadSuccessful = false;
      });
    },
    getFieldNameValidationPromise(name) {
      return this.$http.post('api/harmonization/fieldname_validity', {'fieldname': name});
    },
    /**
     * Trigger login.
     */
    signIn() {
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
        this.$store.dispatch("fetchMailgenTemplates");
        this.$store.dispatch("fetchSettings");
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
    signOut() {
      resetProperties(this);
      this.$store.dispatch('logout');
    },
    /**
     * Trigger a mailgen run
     */
    runMailgen() {
      this.mailgenInProgress = true;
      this.mailgenLog = '';
      let data = {
        verbose: this.mailgenVerbose,
        dry_run: this.mailgenDryRun,
        assigned_columns: this.assignedColumns,
      }
      if (this.mailgenMultiTemplatesEnabled) {
        data.templates = this.mailgenTemplates;
      } else {
        data.template = this.mailgenTemplate;
      }
      this.$http.post('api/mailgen/run', data)
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
          this.showMailgenLog = true;
          return;
        });
    },
    /**
     * Show an Email Template preview with a list of templates (see mailgen_multi_templates_enabled in docs)
     */
    previewMailgen(template_index, showDialog=false) {
      //var me = this;
      this.mailgenInProgress = true;
      this.mailgenLog = '';
      this.$http.post('api/mailgen/preview',
          {
            template: this.mailgenTemplates[template_index]['body'],
            template_name: this.mailgenTemplates[template_index]['name'],
            verbose: this.mailgenVerbose,
            dry_run: this.mailgenDryRun,
            assigned_columns: this.assignedColumns,
            data: this.sendableDataOneRow,
            })
        .then(response => {
          this.mailgenInProgress = false;
          response.json().then(data => {
            console.log('no error and json');
            this.mailgenTemplates[template_index].validationStatus = "text-success";
            this.mailgenPreview = data.result;
            // clear the field, not used in case of success
            this.mailgenTemplates[template_index].validationText = 'Validated OK';
            this.mailgenLog = data.log;

            let [subject, to, body, contentType] = parseMIME(this.mailgenPreview);
            this.mailgenPreviewParsed = {subject: subject, to: to, body: body, contentType: contentType};
            if (showDialog) {
              this.showMailgenPreview = true;
            }
          }).catch(err => {
            console.log('no error and no json')
            // body was not JSON
            this.mailgenTemplates[template_index].validationStatus = "text-danger";
            this.mailgenTemplates[template_index].validationText = "Validation failed";
            this.mailgenLog = err;
            if (showDialog) {
              this.showMailgenLog = true;
            }
            this.mailgenInProgress = false;
        });
        }, (response) => { // error
          response.json().then(data => {
            console.log('error and json')
            this.mailgenPreview = data.result;
            this.mailgenTemplates[template_index].validationStatus = "text-danger";
            this.mailgenTemplates[template_index].validationText = data.result;
            this.mailgenLog = data.log;
            if (showDialog) {
              this.showMailgenLog = true;
            }
            this.mailgenInProgress = false;
          }).catch(err => {
            console.log('error and not json')
            // error response is not JSON
            this.mailgenTemplates[template_index].validationStatus = "text-danger";
            this.mailgenLog = response.body;
            this.mailgenTemplates[template_index].validationText = err;
            if (showDialog) {
              this.showMailgenLog = true;
            }
            this.mailgenInProgress = false;
          })
        });
    },
    /**
     * Show an Email Template preview for the singular mailgen template
     */
    previewMailgenTemplate(showDialog=false) {
      this.mailgenInProgress = true;
      this.mailgenLog = '';
      let previewData = this.sendableDataOneRow;
      previewData = previewData.length ? previewData[0] : {};
      this.$http.post('api/mailgen/preview',
          {
            template: this.mailgenTemplate,
            verbose: this.mailgenVerbose,
            dry_run: this.mailgenDryRun,
            assigned_columns: this.assignedColumns,
            data: previewData,
            })
        .then(response => {
          this.mailgenInProgress = false;
          response.json().then(data => {
            console.log('no error and json')
            this.mailgenTemplateValidationStatus = "text-success";
            this.mailgenPreview = data.result;
            // clear the field, not used in case of success
            this.mailgenTemplateValidationText = 'Validated OK';
            this.mailgenLog = data.log;

            let [subject, to, body, contentType] = parseMIME(this.mailgenPreview)
            this.mailgenPreviewParsed = {subject: subject, to: to, body: body, contentType: contentType}
            if (showDialog) {
              this.showMailgenPreview = true;
            }
          }).catch(err => {
            console.log('no error and no json')
            // body was not JSON
            this.mailgenTemplateValidationStatus = "text-danger";
            this.mailgenTemplateValidationText = "Validation failed";
            this.mailgenLog = err;
            if (showDialog) {
              this.showMailgenLog = true;
            }
            this.mailgenInProgress;
        });
        }, (response) => { // error
          response.json().then(data => {
            console.log('error and json')
            this.mailgenPreview = data.result;
            this.mailgenTemplateValidationStatus = "text-danger";
            this.mailgenTemplateValidationText = data.result;
            this.mailgenLog = data.log;
            if (showDialog) {
              this.showMailgenLog = true;
            }
            this.mailgenInProgress = false;
          }).catch(err => {
            console.log('error and not json')
            // error response is not JSON
            this.mailgenTemplateValidationStatus = "text-danger";
            this.mailgenLog = response.body;
            this.mailgenTemplateValidationText = err;
            if (showDialog) {
              this.showMailgenLog = true;
            }
            this.mailgenInProgress = false;
          })
        });
    },
    /**
     * The debounced validation of the singular mailgen template input
     */
    validateMailgenTemplateContentDebounce: debounce(function () {
      this.previewMailgenTemplate(false)
    }, 1000),
    getRowPromise(row) {
      return this.$http.post('api/bots/process', {
        data: [rowToSendable(row, this.fieldsMap)],
        custom: this.computeCustom(),
        dryrun: this.dryrun,
        timezone: this.timezone,
        assigned_columns: this.assignedColumns,
        templates: this.mailgenMultiTemplatesEnabled ? this.mailgenTemplates : this.mailgenTemplate
      });
    },
    computeCustom() {
      let custom = {};
      if (this.dryrun) {
        custom["custom_classification.type"] = 'test'
      } else {
        custom["custom_classification.type"] = this.classificationType
      }
      // if target groups are available for selection, add the data (even if none selected, then it's an empty list). Otherwise, do not add the data.
      if (this.mailgenAvailableTargetGroupsStatus === true && this.mailgenAvailableTargetGroups && this.mailgenAvailableTargetGroups.tag_values && this.mailgenAvailableTargetGroups.tag_values.length) {
        custom["custom_extra.target_groups"] = this.mailgenTargetGroups.map(value => this.mailgenAvailableTargetGroups.tag_name + ":" + value)
      }
      for (let field of this.customFieldsMapping) {
        if (field.key == 'classification.identifier' && this.dryrun) {
          custom["custom_classification.type"] = 'test'
        } else {
          custom["custom_"+field.key] = field.value;
        }
      }
      return custom;
    },
    /**
     * Increate the number of template inputs
     */
    increaseTemplateCounter() {
      this.mailgenTemplates.push({'name': '', 'body': ''});
      // not really true, but serves the purpose of showing correct "modified" indicator:
      this.mailgenTemplatesServer.push({'name': '', 'body': '', 'validationStatus': null, 'validationText': ''});
    },
    /**
     * Delete a template from the template array
     */
    deleteTemplateInput(index) {
      this.mailgenTemplates.splice(index, 1);
      this.mailgenTemplatesServer.splice(index, 1);
    },
    /**
     * Save a template to disk
     * @param {int} index
     * @param {str} template_name
     * @param {str} template_body
     */
    saveTemplate(index, template_name, template_body) {
      this.$http.put('api/mailgen/template', {
        template_name: template_name,
        template_body: template_body,
      })
        .then(response => {
          response.json().then(data => {
            // success
            console.log('Template save success:', data)
            // update our knowledge of the server template, resets the "changed" indicator
            // https://v2.vuejs.org/v2/guide/reactivity.html#Change-Detection-Caveats
            this.$set(this.mailgenTemplatesServer, index, {name: template_name, body: template_body})
          }).catch(err => {
            // body was not JSON
            this.errorMessage = err;
            this.showErrorModal = true;
        });
        }, (response) => { // error
          this.errorMessage = response.body;
          this.showErrorModal = true;
        });
    },
    /**
     * Show the confirmation dialog for deleting a template
     */
    showTemplateDeletionModal(index, template_name) {
      this.templateToDelete = {'index': index, 'template_name': template_name}
      this.templateDeletionModal = true;
    },
    /**
     * Remove a template from disk and remove it from the UI
     */
    dropTemplate() {
      this.$http.delete('api/mailgen/template', {
        // https://stackoverflow.com/questions/39916939/attaching-data-body-to-http-delete-event-in-vuejs
        body: {template_name: this.templateToDelete.template_name},
      })
        .then(response => {
          response.json().then(data => {
            // success
            console.log('Template deletion success:', data)
            // remove the input field
            this.mailgenTemplates.splice(this.templateToDelete.index, 1);
            // update our knowledge of the server template
            this.mailgenTemplatesServer.splice(this.templateToDelete.index, 1)
            // always reset this variable inside the callbacks, otherwise the variable is reset before it is accessed above for deleting the input, resulting in the first item to be delete (index being null)
            this.templateToDelete = {'index': null, 'template_name': null}
          }).catch(err => {
            // body was not JSON
            this.errorMessage = err;
            this.showErrorModal = true;
            this.templateToDelete = {'index': null, 'template_name': null}
        });
        }, (response) => { // error
          this.errorMessage = response.body;
          this.showErrorModal = true;
          this.templateToDelete = {'index': null, 'template_name': null}
        });
    },
    /**
     * Syntactically validate the template body
     */
    validateTemplateContent: debounce(function (index) {
      this.previewMailgen(index, false)
    }, 1000),
    /**
     * Syntactically validate the template name: check for a duplicate name
     */
    validateTemplateNameDebounced: debounce(function (index) {
      this.validateTemplateName(index)
    }, 200),
    validateTemplateName(index) {
      let templateName = this.mailgenTemplates[index].name;

      let newTemplate = this.mailgenTemplates[index];
      newTemplate.state = true;

      this.mailgenTemplates.forEach(function (template, i) {
        if (i == index) {
          return
        }
        if (template.name == templateName) {
          newTemplate.state = false;
          return
        }
      })
      this.$set(this.mailgenTemplates, index, newTemplate)
    },
    /**
     * onTargetGroupsSelectAll / onTargetGroupsSelectNone
     * Select all or none of the target groups available
     */
    onTargetGroupsSelectAll() {
      this.mailgenTargetGroups = this.mailgenAvailableTargetGroups.tag_values
    },
    onTargetGroupsSelectNone() {
      this.mailgenTargetGroups = [];
    },
    onMailgenTemplatePrototypeSelected() {
      this.mailgenTemplate = this.mailgenTemplateMap[this.mailgenTemplatePrototype];
      // trigger a validation of the template
      this.previewMailgenTemplate(false);
    },
    onShowNotificationAccordion() {
      if (this.mailgenTemplateDefaultTemplateName)
        this.mailgenTemplatePrototype = this.mailgenTemplateDefaultTemplateName;
      else
        this.mailgenTemplatePrototype = this.templates[0].name;
      this.onMailgenTemplatePrototypeSelected()
    }
  },
})
</script>
